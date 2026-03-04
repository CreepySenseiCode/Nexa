"""
Nexa — Splash Screen v9 — ORBITES + PLANÈTE (optimisé).
Effet principal : anneaux orbitaux lumineux autour du logo.
Arrière-plan : grande sphère planétaire avec anneau, trajectoire en arc.
Accents : glow, shine sweep, poussière scintillante.
Fond blanc / fond noir. Fondu de sortie direct.

Optimisations v9 :
  - QElapsedTimer pour delta-temps réel (pas de dérive à 16ms fixe)
  - PreciseTimer pour limiter la gigue
  - Gradients statiques pré-créés (glow central, glow logo)
  - Factorisation setOpacity (une seule fois par section)
  - Scale DPI-aware pour largeurs de traits et taille de police
  - Helper _rotated_ellipse_point pour réduire la duplication
  - Fade-out synchronisé (une seule fenêtre temporelle)
"""

import os
import math
import random

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, QElapsedTimer
from PySide6.QtGui import (
    QPainter,
    QColor,
    QFont,
    QPen,
    QFontMetrics,
    QLinearGradient,
    QRadialGradient,
    QPixmap,
    QPainterPath,
)
from PySide6.QtWidgets import QWidget, QApplication

_LOGO_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "assets",
        "icons",
        "logo_complet_base.png",
    )
)


class SplashScreen(QWidget):
    """Splash screen — orbites + planète, ~3.5s."""

    # ── Palette ──────────────────────────────────────────────────────────
    _BG_LIGHT = QColor("#FFFFFF")
    _BG_DARK = QColor("#0A0E1A")

    _BLUE_100 = QColor("#BBDEFB")
    _BLUE_200 = QColor("#90CAF9")
    _BLUE_300 = QColor("#64B5F6")
    _BLUE_400 = QColor("#42A5F5")
    _BLUE_500 = QColor("#2196F3")
    _BLUE_600 = QColor("#1E88E5")
    _BLUE_700 = QColor("#1976D2")
    _BLUE_800 = QColor("#1565C0")
    _BLUE_900 = QColor("#0D47A1")

    _CYAN = QColor("#00BCD4")
    _CYAN_LIGHT = QColor("#4DD0E1")
    _ELECTRIC = QColor("#2979FF")

    # ── Timing (ms) ──────────────────────────────────────────────────────
    _DURATION = 3000
    _FADE_IN_END = 350  # fin du fade-in
    _FADE_OUT_START = 2600  # début du fade-out unifié
    _FADE_OUT_END = 3000  # fin = durée totale

    def __init__(self, dark_mode=False, parent=None):  # ← parent=None par défaut
        super().__init__(parent)
        self._dark = dark_mode
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)
        W, H = screen.width(), screen.height()

        # ── Scale DPI-aware (base 1080p) ─────────────────────────────────
        self._scale = max(0.6, min(W, H) / 1080.0)

        self._logo = QPixmap(_LOGO_PATH)
        # Calculer les dimensions en respectant le ratio réel de l'image
        if not self._logo.isNull():
            ratio = self._logo.width() / self._logo.height()
            self._lh = int(H * 0.25)
            self._lw = int(self._lh * ratio)
        else:
            self._lh = int(H * 0.25)
            self._lw = int(self._lh * 2.429)

        # ── Timing : QElapsedTimer pour delta réel ───────────────────────
        self._t_ms = 0  # temps écoulé en ms (nommé explicitement)
        self._on_done = None
        self._elapsed = QElapsedTimer()

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

        # ── Pré-calcul gradients statiques ───────────────────────────────
        # (positions calculées au premier paint, alphas mis à jour par frame)
        self._glow_bg_cached = None  # QRadialGradient pour le glow central
        self._glow_logo_cached = None  # QRadialGradient pour le glow logo

        random.seed(42)
        self._orbits = []
        self._dust = []
        self._init_orbits(W, H)

    def _init_orbits(self, W, H):
        """3 anneaux orbitaux autour du logo."""
        base = min(W, H)

        self._orbits = [
            {
                "rx": base * 0.34,
                "ry_ratio": 0.28,  # ellipse aplatie → vue inclinée
                "tilt": -18,  # inclinaison en degrés
                "speed": 0.0020,  # rad/ms, sens horaire
                "color": self._CYAN,
                "ring_color": self._CYAN_LIGHT,
                "orbs": [
                    {"phase": 0.0, "size": 7.5},
                    {"phase": math.pi, "size": 5.0},  # à l'opposé
                ],
                "trail_steps": 42,
            },
            {
                "rx": base * 0.43,  # orbite la plus large
                "ry_ratio": 0.22,  # très aplatie
                "tilt": 12,
                "speed": -0.0015,  # sens anti-horaire
                "color": self._ELECTRIC,
                "ring_color": self._BLUE_400,
                "orbs": [
                    {"phase": math.pi * 0.5, "size": 6.5},
                    {"phase": math.pi * 1.5, "size": 4.0},
                ],
                "trail_steps": 38,
            },
            {
                "rx": base * 0.27,  # orbite interne
                "ry_ratio": 0.35,
                "tilt": -45,  # fortement inclinée
                "speed": 0.0028,  # la plus rapide
                "color": self._BLUE_500,
                "ring_color": self._BLUE_300,
                "orbs": [
                    {"phase": math.pi * 0.3, "size": 6.0},
                ],
                "trail_steps": 32,
            },
        ]

        # Poussière scintillante le long des orbites
        for orb_def in self._orbits:
            rx = orb_def["rx"]
            ry = rx * orb_def["ry_ratio"]
            tilt_rad = math.radians(orb_def["tilt"])
            for _ in range(20):
                angle = random.uniform(0, math.tau)
                dx, dy = self._rotated_ellipse_point(rx, ry, tilt_rad, angle)
                dx += random.uniform(-18, 18)
                dy += random.uniform(-18, 18)
                self._dust.append(
                    {
                        "dx": dx,
                        "dy": dy,
                        "r": random.uniform(0.8, 2.5),
                        "phase": random.uniform(0, math.tau),
                        "speed": random.uniform(0.004, 0.009),
                        "alpha_max": random.randint(60, 160),
                        "delay": random.randint(500, 1600),
                    }
                )

    @property
    def _bg(self):
        return self._BG_DARK if self._dark else self._BG_LIGHT

    def start(self, on_done=None):
        self._on_done = on_done
        self._t_ms = 0
        self._elapsed.start()
        self.showFullScreen()
        self._timer.start()

    # ── Easings ──────────────────────────────────────────────────────────
    @staticmethod
    def _ease_out(t):
        """Ease-out cubique (décélération douce)."""
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _ease_io(t):
        """Ease-in-out Hermite (accélère puis décélère)."""
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def _ease_back(t):
        """Ease-out avec léger overshoot (bounce subtil)."""
        c1, c3 = 1.70158, 2.70158
        return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2

    def _p(self, t0, t1, ease=None):
        """Progression normalisée [0,1] entre t0 et t1 ms, avec easing optionnel."""
        if self._t_ms <= t0:
            return 0.0
        if self._t_ms >= t1:
            return 1.0
        v = (self._t_ms - t0) / (t1 - t0)
        return ease(v) if ease else v

    def _tick(self):
        """Tick basé sur le temps réel via QElapsedTimer (pas de dérive 16ms)."""
        self._t_ms = self._elapsed.elapsed()
        self.update()
        if self._t_ms >= self._DURATION:
            self._timer.stop()
            self.hide()  # masque immédiatement pour éviter le flash gris
            self.close()
            if self._on_done:
                self._on_done()

    # ── Helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _rotated_ellipse_point(rx, ry, tilt_rad, angle):
        """Point sur une ellipse (rx, ry) tournée de tilt_rad."""
        ex = math.cos(angle) * rx
        ey = math.sin(angle) * ry
        px = ex * math.cos(tilt_rad) - ey * math.sin(tilt_rad)
        py = ex * math.sin(tilt_rad) + ey * math.cos(tilt_rad)
        return px, py

    def _orbit_point(self, orb_def, angle):
        """Point sur l'orbite d'un orb_def donné."""
        rx = orb_def["rx"]
        ry = rx * orb_def["ry_ratio"]
        tilt_rad = math.radians(orb_def["tilt"])
        return self._rotated_ellipse_point(rx, ry, tilt_rad, angle)

    @staticmethod
    def _circle_path(center, radius):
        path = QPainterPath()
        path.addEllipse(center, radius, radius)
        return path

    def _dm(self, light_val, dark_val):
        """Retourne light_val ou dark_val selon le mode."""
        return dark_val if self._dark else light_val

    def _build_glow_bg(self, logo_cx, logo_cy, W, H):
        """Construit le gradient du glow central (une seule fois)."""
        rg = QRadialGradient(QPointF(logo_cx, logo_cy), max(W, H) * 0.45)
        # Alphas à 1.0 — seront modulés par setOpacity à chaque frame
        base_a = self._dm(50, 80)
        rg.setColorAt(0.0, QColor(33, 150, 243, base_a))
        rg.setColorAt(0.35, QColor(0, 188, 212, int(base_a * 0.4)))
        rg.setColorAt(1.0, QColor(0, 0, 0, 0))
        return rg

    def _build_glow_logo(self, logo_cx, logo_cy, lw, lh):
        """Construit le gradient du glow logo (une seule fois)."""
        lg = QRadialGradient(QPointF(logo_cx, logo_cy), max(lw, lh) * 0.48)
        base_a = self._dm(35, 65)
        lg.setColorAt(0.2, QColor(0, 188, 212, base_a))
        lg.setColorAt(1.0, QColor(0, 188, 212, 0))
        return lg

    # ── Paint ────────────────────────────────────────────────────────────
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        W, H = self.width(), self.height()
        cx, cy = W / 2.0, H / 2.0
        sc = self._scale  # facteur DPI

        # ── Fade unifié : tout part ensemble ─────────────────────────────
        fade_in = self._p(0, self._FADE_IN_END, self._ease_io)
        fade_out = 1.0 - self._p(
            self._FADE_OUT_START, self._FADE_OUT_END, self._ease_io
        )
        go = fade_in * fade_out  # opacité globale unique

        # Logo geometry
        lw, lh = self._lw, self._lh
        lx = cx - lw / 2.0
        ly = cy - lh / 2.0 - H * 0.035
        logo_cx = lx + lw / 2.0
        logo_cy = ly + lh / 2.0

        # ── Cache des gradients statiques (1er frame uniquement) ─────────
        if self._glow_bg_cached is None:
            self._glow_bg_cached = self._build_glow_bg(logo_cx, logo_cy, W, H)
        if self._glow_logo_cached is None:
            self._glow_logo_cached = self._build_glow_logo(logo_cx, logo_cy, lw, lh)

        # ━━ FOND ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        p.setOpacity(go)
        p.fillRect(self.rect(), self._bg)

        # ━━ PLANÈTE — grosse sphère en arrière-plan ━━━━━━━━━━━━━━━━━━━━
        planet_appear = self._p(0, 600, self._ease_out)
        planet_op = planet_appear * fade_out

        if planet_op > 0:
            # Trajectoire en arc de cercle passant derrière le logo
            travel = self._p(0, 3500, self._ease_io)
            planet_r = min(W, H) * 0.14

            # Arc : centre bien en dessous, grand rayon → courbe douce
            arc_cx = cx  # centré horizontalement
            arc_cy = cy + H * 0.65  # pivot très bas (hors écran)
            arc_radius = H * 0.85  # rayon large → arc peu courbé
            start_angle = math.pi * 0.82  # ~148° départ gauche
            end_angle = math.pi * 0.18  # ~32° arrivée droite
            current_arc_angle = start_angle + (end_angle - start_angle) * travel

            px = arc_cx + math.cos(current_arc_angle) * arc_radius
            py = arc_cy - math.sin(current_arc_angle) * arc_radius

            p.setOpacity(go)

            # ── Halo planétaire (glow très large) ────────────────────────
            halo_r = planet_r * 4.5
            hg = QRadialGradient(QPointF(px, py), halo_r)
            ha = int(self._dm(18, 35) * planet_op)
            hg.setColorAt(0.0, QColor(33, 150, 243, ha))
            hg.setColorAt(0.3, QColor(0, 188, 212, int(ha * 0.5)))
            hg.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.fillPath(self._circle_path(QPointF(px, py), halo_r), hg)

            # ── Sphère planétaire (dégradé 3D) ──────────────────────────
            sphere_grad = QRadialGradient(
                QPointF(
                    px - planet_r * 0.3, py - planet_r * 0.3
                ),  # lumière haut-gauche
                planet_r * 1.3,
            )
            ba = int(self._dm(50, 90) * planet_op)
            sphere_grad.setColorAt(
                0.0,
                QColor(
                    self._BLUE_200.red(),
                    self._BLUE_200.green(),
                    self._BLUE_200.blue(),
                    int(ba * 1.2),
                ),
            )
            sphere_grad.setColorAt(
                0.45,
                QColor(
                    self._BLUE_400.red(),
                    self._BLUE_400.green(),
                    self._BLUE_400.blue(),
                    ba,
                ),
            )
            sphere_grad.setColorAt(
                0.85,
                QColor(
                    self._BLUE_700.red(),
                    self._BLUE_700.green(),
                    self._BLUE_700.blue(),
                    int(ba * 0.8),
                ),
            )
            sphere_grad.setColorAt(
                1.0,
                QColor(
                    self._BLUE_900.red(),
                    self._BLUE_900.green(),
                    self._BLUE_900.blue(),
                    0,
                ),
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(sphere_grad)
            p.drawEllipse(QPointF(px, py), planet_r, planet_r)

            # ── Reflet spéculaire ────────────────────────────────────────
            spec_x = px - planet_r * 0.28
            spec_y = py - planet_r * 0.28
            spec_r = planet_r * 0.35
            spec_grad = QRadialGradient(QPointF(spec_x, spec_y), spec_r)
            spec_a = int(self._dm(55, 80) * planet_op)
            spec_grad.setColorAt(0.0, QColor(255, 255, 255, spec_a))
            spec_grad.setColorAt(0.5, QColor(200, 230, 255, int(spec_a * 0.3)))
            spec_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.fillPath(self._circle_path(QPointF(spec_x, spec_y), spec_r), spec_grad)

            # ── Anneau planétaire (rappel du logo N + anneau) ────────────
            ring_rx = planet_r * 1.9
            ring_ry = planet_r * 0.35
            ring_tilt_deg = -25.0  # inclinaison de l'anneau

            self._draw_planet_ring_half(
                p,
                px,
                py,
                ring_rx,
                ring_ry,
                ring_tilt_deg,
                planet_op,
                go,
                sc,
                behind=True,
            )
            self._draw_planet_ring_half(
                p,
                px,
                py,
                ring_rx,
                ring_ry,
                ring_tilt_deg,
                planet_op,
                go,
                sc,
                behind=False,
            )

            # ── Traînée lumineuse (suit l'arc) ───────────────────────────
            p.setPen(Qt.PenStyle.NoPen)
            trail_count = 25
            for ti in range(trail_count):
                t_progress = ti / trail_count
                t_travel = max(0, travel - t_progress * 0.12)
                t_arc_angle = start_angle + (end_angle - start_angle) * t_travel
                t_px = arc_cx + math.cos(t_arc_angle) * arc_radius
                t_py = arc_cy - math.sin(t_arc_angle) * arc_radius

                t_alpha = int(self._dm(12, 22) * planet_op * (1.0 - t_progress) ** 2)
                t_r = planet_r * (0.6 - 0.5 * t_progress)
                if t_alpha < 2 or t_r < 1:
                    continue

                tc = QColor(self._BLUE_300)
                tc.setAlpha(t_alpha)
                p.setBrush(tc)
                p.drawEllipse(QPointF(t_px, t_py), t_r, t_r)

        # ━━ GLOW CENTRAL (gradient caché, opacité modulée) ━━━━━━━━━━━━
        glow_bg = self._p(100, 800, self._ease_out) * fade_out
        if glow_bg > 0:
            p.setOpacity(go * glow_bg * 0.55)
            p.fillRect(self.rect(), self._glow_bg_cached)

        # ━━ ORBITES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        orb_appear = self._p(300, 1100, self._ease_out)
        orb_op = orb_appear * fade_out

        if orb_op > 0:
            p.setOpacity(go)
            for oidx, orb_def in enumerate(self._orbits):
                delay_ms = oidx * 150  # 0ms, 150ms, 300ms d'écart
                local_appear = self._p(300 + delay_ms, 1100 + delay_ms, self._ease_out)
                if local_appear <= 0:
                    continue
                local_op = local_appear * fade_out

                rx = orb_def["rx"]
                ry = rx * orb_def["ry_ratio"]

                # ── Anneau orbital visible ───────────────────────────────
                ring_alpha = self._dm(25, 50) * local_op
                if ring_alpha > 1:
                    rc = QColor(orb_def["ring_color"])
                    rc.setAlpha(int(ring_alpha))
                    # Largeur relative au DPI (clamp 1.0–2.5)
                    ring_w = max(1.0, min(2.5, 1.4 * sc))
                    p.setPen(QPen(rc, ring_w))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.save()
                    p.translate(logo_cx, logo_cy)
                    p.rotate(orb_def["tilt"])
                    p.drawEllipse(QPointF(0, 0), rx, ry)
                    p.restore()

                # ── Orbes + traînées ─────────────────────────────────────
                p.setPen(Qt.PenStyle.NoPen)
                for orb in orb_def["orbs"]:
                    current_angle = orb["phase"] + self._t_ms * orb_def["speed"]

                    # Traînée
                    trail_n = orb_def["trail_steps"]
                    step_angle = orb_def["speed"] * 18  # écart entre points de traînée
                    for ti in range(trail_n, 0, -1):
                        trail_angle = current_angle - step_angle * ti
                        ttx, tty = self._orbit_point(orb_def, trail_angle)
                        ttx += logo_cx
                        tty += logo_cy

                        trail_p = 1.0 - (ti / trail_n)  # 0=bout, 1=tête
                        ta = int(self._dm(110, 170) * local_op * (trail_p**1.8))
                        tr = orb["size"] * (0.15 + 0.85 * trail_p**1.5) * 0.6
                        if ta < 2:
                            continue

                        tc = QColor(orb_def["color"])
                        tc.setAlpha(ta)
                        p.setBrush(tc)
                        p.drawEllipse(QPointF(ttx, tty), tr, tr)

                    # Orbe principal
                    ox, oy = self._orbit_point(orb_def, current_angle)
                    ox += logo_cx
                    oy += logo_cy

                    # Halo externe
                    halo_r = orb["size"] * 5.0
                    hg = QRadialGradient(QPointF(ox, oy), halo_r)
                    ha = int(self._dm(45, 75) * local_op)
                    hg.setColorAt(
                        0.0,
                        QColor(
                            orb_def["color"].red(),
                            orb_def["color"].green(),
                            orb_def["color"].blue(),
                            ha,
                        ),
                    )
                    hg.setColorAt(
                        0.4,
                        QColor(
                            orb_def["color"].red(),
                            orb_def["color"].green(),
                            orb_def["color"].blue(),
                            int(ha * 0.3),
                        ),
                    )
                    hg.setColorAt(1.0, QColor(0, 0, 0, 0))
                    p.fillPath(self._circle_path(QPointF(ox, oy), halo_r), hg)

                    # Noyau lumineux (blanc au centre → couleur → transparent)
                    core_r = orb["size"]
                    cg = QRadialGradient(QPointF(ox, oy), core_r)
                    ca = int(self._dm(230, 255) * local_op)
                    cg.setColorAt(0.0, QColor(255, 255, 255, int(ca * 0.9)))
                    cg.setColorAt(
                        0.3,
                        QColor(
                            orb_def["color"].red(),
                            orb_def["color"].green(),
                            orb_def["color"].blue(),
                            ca,
                        ),
                    )
                    cg.setColorAt(
                        1.0,
                        QColor(
                            orb_def["color"].red(),
                            orb_def["color"].green(),
                            orb_def["color"].blue(),
                            0,
                        ),
                    )
                    p.fillPath(self._circle_path(QPointF(ox, oy), core_r * 1.8), cg)

        # ━━ POUSSIÈRE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        dust_op = orb_op
        if dust_op > 0:
            p.setOpacity(go)
            p.setPen(Qt.PenStyle.NoPen)
            # Désactiver l'AA pour les petites particules (gain perf)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            for d in self._dust:
                if self._t_ms < d["delay"]:
                    continue
                pulse = 0.5 + 0.5 * math.sin(self._t_ms * d["speed"] + d["phase"])
                da = int(d["alpha_max"] * dust_op * pulse)
                # Boost light mode (+20%), boost dark mode (+50%)
                if self._dark:
                    da = min(255, int(da * 1.5))
                else:
                    da = min(255, int(da * 1.2))
                if da < 3:
                    continue
                dc = QColor(self._CYAN_LIGHT)
                dc.setAlpha(da)
                p.setBrush(dc)
                dr = d["r"] * (0.6 + 0.4 * pulse)
                p.drawEllipse(QPointF(logo_cx + d["dx"], logo_cy + d["dy"]), dr, dr)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # ━━ LOGO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logo_in = self._p(400, 1100, self._ease_out)
        logo_scale_p = self._p(400, 1050, self._ease_back)

        if logo_in > 0 and not self._logo.isNull():
            p.save()
            p.setOpacity(go * min(logo_in * 2.5, 1.0))

            # Reveal circulaire depuis le centre
            max_r = math.sqrt(lw * lw + lh * lh) * 0.55
            clip_r = max_r * logo_in
            clip = QPainterPath()
            clip.addEllipse(QPointF(logo_cx, logo_cy), clip_r, clip_r)
            p.setClipPath(clip)

            # Scale bounce (0.88 → 1.0 avec overshoot subtil)
            s = 0.88 + 0.12 * logo_scale_p
            p.translate(logo_cx, logo_cy)
            p.scale(s, s)
            p.translate(-logo_cx, -logo_cy)

            p.drawPixmap(int(lx), int(ly), int(lw), int(lh), self._logo)
            p.restore()

            # Glow du logo (gradient caché, opacité modulée)
            glow_logo = self._p(700, 1400, self._ease_out) * fade_out
            if glow_logo > 0:
                p.setOpacity(go * glow_logo * 0.5)
                p.fillRect(self.rect(), self._glow_logo_cached)

        # ━━ SHINE SWEEP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        shine_p = self._p(1400, 2000, self._ease_io)
        if shine_p > 0 and logo_in > 0.95:  # seuil souple (évite edge case =1.0)
            p.save()
            sx = lx - 120 + (lw + 240) * shine_p
            sg = QLinearGradient(sx - 60, 0, sx + 60, 0)
            bright = self._dm(80, 50)
            peak = self._dm(130, 85)
            sg.setColorAt(0.0, QColor(255, 255, 255, 0))
            sg.setColorAt(0.35, QColor(255, 255, 255, bright))
            sg.setColorAt(0.50, QColor(210, 240, 255, peak))
            sg.setColorAt(0.65, QColor(255, 255, 255, bright))
            sg.setColorAt(1.0, QColor(255, 255, 255, 0))
            clip = QPainterPath()
            clip.addRect(QRectF(lx, ly, lw, lh))
            p.setClipPath(clip)
            p.setOpacity(go * 0.8)
            p.fillRect(QRectF(sx - 60, ly, 120, lh), sg)
            p.restore()

        # ━━ TEXTE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        text_in = self._p(1500, 2100, self._ease_out)
        text_op = text_in * fade_out
        if text_op > 0.01:
            tfont = QApplication.font()
            # Taille relative au DPI (pixelSize pour cohérence multi-écran)
            tfont.setPixelSize(max(12, int(18 * sc)))
            tfont.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 10.0 * sc)
            tfont.setWeight(QFont.Weight.Light)
            p.setFont(tfont)
            fm = QFontMetrics(tfont)
            text = "GESTION DE CLIENTÈLE"
            tw = fm.horizontalAdvance(text)
            tx = cx - tw / 2.0
            ty = ly + lh + H * 0.055

            # Ligne décorative (dégradé horizontal, estompée aux bords)
            line_y = ty - H * 0.018
            line_w = tw * 1.2 * min(text_in * 1.5, 1.0)
            lc = QColor(self._dm(self._BLUE_300, self._BLUE_600))
            lc.setAlpha(int(90 * text_op))
            lg = QLinearGradient(cx - line_w / 2, 0, cx + line_w / 2, 0)
            lc0 = QColor(lc)
            lc0.setAlpha(0)
            lg.setColorAt(0.0, lc0)
            lg.setColorAt(0.25, lc)
            lg.setColorAt(0.75, lc)
            lg.setColorAt(1.0, lc0)
            p.setOpacity(go)
            line_pen_w = max(1.0, 1.2 * sc)
            p.setPen(QPen(lg, line_pen_w))
            p.drawLine(
                QPointF(cx - line_w / 2, line_y),
                QPointF(cx + line_w / 2, line_y),
            )

            # Texte
            tc = QColor(self._dm(self._BLUE_700, self._BLUE_200))
            p.setOpacity(go * text_op)
            p.setPen(QPen(tc))
            p.drawText(int(tx), int(ty), text)

        p.end()

    # ── Dessin de l'anneau planétaire (moitié avant ou arrière) ──────────
    def _draw_planet_ring_half(
        self, p, px, py, ring_rx, ring_ry, tilt_deg, planet_op, go, sc, behind
    ):
        """Dessine la moitié avant ou arrière de l'anneau de la planète."""
        tilt_rad = math.radians(tilt_deg)
        segments = 80
        # Largeur du trait proportionnelle au DPI
        ring_width = max(1.5, self._dm(2.0, 2.5) * sc)

        p.setOpacity(go)

        for i in range(segments):
            angle = (i / segments) * math.tau
            next_angle = ((i + 1) / segments) * math.tau

            # Déterminer si ce segment est devant ou derrière la planète
            local_y = math.sin(angle) * ring_ry
            rotated_y = math.cos(angle) * ring_rx * math.sin(
                tilt_rad
            ) + local_y * math.cos(tilt_rad)

            if behind and rotated_y > 0:
                continue  # segment devant → skip
            if not behind and rotated_y <= 0:
                continue  # segment derrière → skip

            # Points de début et fin du segment
            rx1, ry1 = self._rotated_ellipse_point(ring_rx, ring_ry, tilt_rad, angle)
            rx2, ry2 = self._rotated_ellipse_point(
                ring_rx, ring_ry, tilt_rad, next_angle
            )

            # Alpha plus lumineux sur les côtés (face à la caméra)
            side_factor = abs(math.cos(angle))
            alpha = int(self._dm(40, 70) * planet_op * (0.3 + 0.7 * side_factor))
            if alpha < 2:
                continue

            rc = QColor(self._BLUE_300)
            rc.setAlpha(alpha)
            pen = QPen(rc, ring_width * (0.5 + 0.5 * side_factor))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(px + rx1, py + ry1), QPointF(px + rx2, py + ry2))

        # Glow subtil sur l'anneau avant uniquement
        if not behind:
            ring_glow_r = max(ring_rx, ring_ry) * 1.1
            rg = QRadialGradient(QPointF(px, py), ring_glow_r)
            rga = int(self._dm(10, 20) * planet_op)
            rg.setColorAt(0.6, QColor(100, 180, 255, rga))
            rg.setColorAt(0.85, QColor(100, 180, 255, int(rga * 0.4)))
            rg.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.fillPath(self._circle_path(QPointF(px, py), ring_glow_r), rg)
