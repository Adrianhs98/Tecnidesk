import { memo, useEffect, useRef } from "react";

/**
 * LandingAmbientTech (Global Canvas 2D Dynamic Neural Particle Network)
 * - Single global fixed instance mounted in LandingLayout.
 * - Discrete particle density calibrated for atmosphere without content competition:
 *   - Desktop: ~34 nodes (30-40 range)
 *   - Tablet: ~24 nodes (22-28 range)
 *   - Mobile: ~14 nodes (12-18 range)
 * - Real-time section detection via lightweight IntersectionObserver (zero scroll listeners).
 * - Smooth exponential lerp of render intensity, visual density, and connection radius:
 *   - Hero ≈ 0.40
 *   - Problema ≈ 0.20
 *   - Workflow / Workbench ≈ 1.00
 *   - Ohm Copiloto ≈ 0.90
 *   - Acompañamiento Humano ≈ 0.10
 *   - Piloto / Contacto ≈ 0.10
 * - Continuous, uninterrupted Brownian drift across section transitions.
 * - Pauses rAF on document.hidden (visibilitychange).
 * - Full prefers-reduced-motion support (single static frame, 0 animation loops).
 * - Zero React state re-renders during animation.
 */
function LandingAmbientTech() {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext?.("2d");
    if (!ctx) return;

    let rafId = null;
    let isVisible = true;
    let isTabVisible = typeof document !== "undefined" ? !document.hidden : true;
    let width = 0;
    let height = 0;
    let lastTime = performance.now();

    const prefersReducedMotion =
      typeof window !== "undefined" &&
      Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);

    // TecniDesk theme palette (Slate neutral, Amber accent, Green success)
    let themeColors = {
      neutral: { r: 140, g: 145, b: 155 },
      accent: { r: 240, g: 136, b: 62 },
      success: { r: 63, g: 185, b: 80 },
    };

    function updateThemeColors() {
      if (typeof window === "undefined") return;
      try {
        const isDark =
          document.documentElement.getAttribute("data-theme") === "dark" ||
          (!document.documentElement.getAttribute("data-theme") &&
            window.matchMedia?.("(prefers-color-scheme: dark)")?.matches);

        if (isDark) {
          themeColors = {
            neutral: { r: 156, g: 163, b: 175 },
            accent: { r: 240, g: 136, b: 62 },
            success: { r: 63, g: 185, b: 80 },
          };
        } else {
          themeColors = {
            neutral: { r: 107, g: 114, b: 128 },
            accent: { r: 217, g: 107, b: 24 },
            success: { r: 46, g: 140, b: 60 },
          };
        }
      } catch {}
    }

    updateThemeColors();

    // Section intensity mapping
    const SECTION_TARGETS = {
      hero: { intensity: 0.40, tone: "neutral" },
      top: { intensity: 0.40, tone: "neutral" },
      solucion: { intensity: 0.20, tone: "neutral" },
      workbench: { intensity: 1.00, tone: "workbench" },
      ohm: { intensity: 0.90, tone: "ohm" },
      beneficios: { intensity: 0.10, tone: "neutral" },
      piloto: { intensity: 0.10, tone: "neutral" },
      postular: { intensity: 0.10, tone: "neutral" },
    };

    let currentIntensity = 0.40;
    let targetIntensity = 0.40;
    let currentTone = "neutral";
    let particles = [];

    function initParticles() {
      if (width <= 0 || height <= 0) return;

      // Discreet density constraint
      let count = 34; // Desktop (30-40)
      if (width < 768) {
        count = 14; // Mobile (12-18)
      } else if (width < 1024) {
        count = 24; // Tablet (22-28)
      }

      particles = [];

      for (let i = 0; i < count; i++) {
        const x = Math.random() * width;
        const y = Math.random() * height;
        const angle = Math.random() * Math.PI * 2;
        const speed = 0.15 + Math.random() * 0.22; // Organic slow ambient drift

        particles.push({
          x,
          y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          radius: 1.5 + Math.random() * 1.1,
          baseAlpha: 0.22 + Math.random() * 0.18,
          wanderAngle: angle,
          wanderSpeed: 0.015 + Math.random() * 0.02,
          pulsePhase: Math.random() * Math.PI * 2,
        });
      }
    }

    function resize() {
      const w = window.innerWidth || document.documentElement.clientWidth || 1024;
      const h = window.innerHeight || document.documentElement.clientHeight || 768;
      if (w <= 0 || h <= 0) return;

      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = w;
      height = h;

      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      initParticles();

      if (prefersReducedMotion) {
        drawFrame(0, 0);
      }
    }

    const handleWindowResize = () => resize();
    window.addEventListener("resize", handleWindowResize);
    resize();

    function getDistanceThreshold() {
      if (width < 768) return 92;
      if (width < 1024) return 118;
      return 140;
    }

    function drawFrame(now, dt) {
      if (width <= 0 || height <= 0) return;

      ctx.clearRect(0, 0, width, height);

      // Smooth exponential lerp towards target intensity (frame-rate independent)
      if (!prefersReducedMotion && dt > 0) {
        const dtClamped = Math.min(Math.max(dt, 0), 100);
        const lerpFactor = 1 - Math.exp(-dtClamped * 0.0035);
        currentIntensity += (targetIntensity - currentIntensity) * lerpFactor;
      } else {
        currentIntensity = targetIntensity;
      }

      const D = getDistanceThreshold();
      // Distance scales with intensity: ~70% in Piloto/Cualitativo up to 100% in Workbench
      const effectiveD = D * (0.68 + 0.32 * currentIntensity);
      const numParticles = particles.length;

      // 1. Update particle physics & positions
      if (!prefersReducedMotion && dt > 0) {
        const dtRatio = Math.min(dt / 16.67, 2.5);

        for (let i = 0; i < numParticles; i++) {
          const p = particles[i];

          // Continuous organic trajectory steering
          p.wanderAngle += (Math.random() - 0.5) * p.wanderSpeed;
          p.vx += Math.cos(p.wanderAngle) * 0.025 * dtRatio;
          p.vy += Math.sin(p.wanderAngle) * 0.025 * dtRatio;

          // Soft speed capping
          const currentSpeed = Math.hypot(p.vx, p.vy);
          if (currentSpeed > 0.52) {
            p.vx = (p.vx / currentSpeed) * 0.52;
            p.vy = (p.vy / currentSpeed) * 0.52;
          } else if (currentSpeed < 0.12) {
            p.vx = (p.vx / (currentSpeed || 1)) * 0.15;
            p.vy = (p.vy / (currentSpeed || 1)) * 0.15;
          }

          // Soft boundary steering
          const margin = 24;
          if (p.x < margin) p.vx += 0.03 * dtRatio;
          if (p.x > width - margin) p.vx -= 0.03 * dtRatio;
          if (p.y < margin) p.vy += 0.03 * dtRatio;
          if (p.y > height - margin) p.vy -= 0.03 * dtRatio;

          // Safety wrap/clamp
          if (p.x < 0) { p.x = 0; p.vx = Math.abs(p.vx); }
          if (p.x > width) { p.x = width; p.vx = -Math.abs(p.vx); }
          if (p.y < 0) { p.y = 0; p.vy = Math.abs(p.vy); }
          if (p.y > height) { p.y = height; p.vy = -Math.abs(p.vy); }

          p.x += p.vx * dtRatio;
          p.y += p.vy * dtRatio;
        }
      }

      // 2. Dynamic proximity connections (1 to 3 neighbors per node)
      const candidateEdges = [];
      for (let i = 0; i < numParticles; i++) {
        for (let j = i + 1; j < numParticles; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.hypot(dx, dy);
          if (dist < effectiveD) {
            candidateEdges.push({ i, j, dist });
          }
        }
      }

      candidateEdges.sort((a, b) => a.dist - b.dist);

      const degrees = new Uint8Array(numParticles);
      const maxDegree = width < 768 ? 2 : 3;

      ctx.lineWidth = 0.85;

      for (let k = 0; k < candidateEdges.length; k++) {
        const { i, j, dist } = candidateEdges[k];
        if (degrees[i] >= maxDegree || degrees[j] >= maxDegree) continue;

        degrees[i]++;
        degrees[j]++;

        const p1 = particles[i];
        const p2 = particles[j];

        const proximity = 1 - dist / effectiveD;
        const alphaFade = proximity * proximity;

        let edgeColor = themeColors.neutral;
        let edgeAlpha = alphaFade * (0.05 + 0.22 * currentIntensity);

        // Contextual accenting
        if (currentTone === "ohm" && currentIntensity > 0.5) {
          // Ohm amber focal accents
          if ((i + j) % 3 === 0) {
            edgeColor = themeColors.accent;
            edgeAlpha = alphaFade * (0.08 + 0.28 * currentIntensity);
          }
        } else if (currentTone === "workbench" && currentIntensity > 0.6) {
          // Workbench accent accents
          if ((i + j) % 4 === 0) {
            edgeColor = themeColors.accent;
            edgeAlpha = alphaFade * (0.08 + 0.26 * currentIntensity);
          }
        }

        ctx.strokeStyle = `rgba(${edgeColor.r}, ${edgeColor.g}, ${edgeColor.b}, ${edgeAlpha.toFixed(3)})`;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }

      // 3. Draw particles & contextual halos
      const timeSec = now * 0.001;

      for (let i = 0; i < numParticles; i++) {
        const p = particles[i];

        let nodeColor = themeColors.neutral;
        let nodeAlpha = p.baseAlpha * (0.28 + 0.72 * currentIntensity);
        let hasHalo = false;
        let haloColor = themeColors.accent;

        if (currentTone === "ohm" && currentIntensity > 0.6) {
          if (i === 1 || i === 4) {
            nodeColor = themeColors.accent;
            nodeAlpha = Math.min(nodeAlpha + 0.25, 0.75);
            hasHalo = true;
          }
        } else if (currentTone === "workbench" && currentIntensity > 0.7) {
          if (i === 2) {
            nodeColor = themeColors.accent;
            nodeAlpha = Math.min(nodeAlpha + 0.25, 0.75);
            hasHalo = true;
          } else if (i === 5) {
            nodeColor = themeColors.success;
            haloColor = themeColors.success;
            nodeAlpha = Math.min(nodeAlpha + 0.25, 0.75);
            hasHalo = true;
          }
        }

        ctx.fillStyle = `rgba(${nodeColor.r}, ${nodeColor.g}, ${nodeColor.b}, ${nodeAlpha.toFixed(3)})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();

        if (hasHalo && !prefersReducedMotion) {
          const breathe = Math.sin(timeSec * 2.2 + p.pulsePhase) * 1.5;
          const haloRadius = p.radius + 3.2 + breathe;
          const haloAlpha = (0.16 + Math.sin(timeSec * 2.2 + p.pulsePhase) * 0.08) * currentIntensity;

          ctx.strokeStyle = `rgba(${haloColor.r}, ${haloColor.g}, ${haloColor.b}, ${Math.max(haloAlpha, 0.03).toFixed(3)})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(p.x, p.y, haloRadius, 0, Math.PI * 2);
          ctx.stroke();
        }
      }
    }

    function loop(now) {
      if (!isVisible || !isTabVisible) {
        rafId = null;
        return;
      }

      const dt = now - lastTime;
      lastTime = now;

      drawFrame(now, dt);

      rafId = requestAnimationFrame(loop);
    }

    // Section Observer for continuous narrative intensity
    const sectionIds = ["hero", "solucion", "workbench", "ohm", "beneficios", "piloto", "postular"];
    let sectionObserver = null;

    if (typeof IntersectionObserver !== "undefined") {
      const sectionRatios = new Map();

      sectionObserver = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            const id = entry.target.id;
            if (entry.isIntersecting) {
              sectionRatios.set(id, entry.intersectionRatio);
            } else {
              sectionRatios.delete(id);
            }
          }

          let dominantId = null;
          let maxRatio = 0;
          for (const [id, ratio] of sectionRatios.entries()) {
            if (ratio > maxRatio) {
              maxRatio = ratio;
              dominantId = id;
            }
          }

          if (dominantId && SECTION_TARGETS[dominantId]) {
            targetIntensity = SECTION_TARGETS[dominantId].intensity;
            currentTone = SECTION_TARGETS[dominantId].tone;
          } else if (typeof window !== "undefined" && window.scrollY < 200) {
            targetIntensity = 0.40;
            currentTone = "neutral";
          }
        },
        {
          threshold: [0.05, 0.2, 0.4, 0.6, 0.8],
          rootMargin: "-10% 0px -15% 0px",
        }
      );

      sectionIds.forEach((id) => {
        const el = document.getElementById(id);
        if (el) sectionObserver.observe(el);
      });
    }

    // VisibilityChange to freeze rAF when tab is hidden
    function handleVisibilityChange() {
      isTabVisible = !document.hidden;
      if (!isTabVisible) {
        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
      } else {
        if (!rafId && isVisible && !prefersReducedMotion) {
          lastTime = performance.now();
          rafId = requestAnimationFrame(loop);
        }
      }
    }
    document.addEventListener("visibilitychange", handleVisibilityChange);

    // Initial rAF trigger
    if (!prefersReducedMotion) {
      rafId = requestAnimationFrame(loop);
    }

    let themeObserver = null;
    if (typeof MutationObserver !== "undefined") {
      themeObserver = new MutationObserver(() => {
        updateThemeColors();
      });
      themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["data-theme"],
      });
    }

    return () => {
      window.removeEventListener("resize", handleWindowResize);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (rafId) cancelAnimationFrame(rafId);
      if (sectionObserver) sectionObserver.disconnect();
      if (themeObserver) themeObserver.disconnect();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="landing-ambient-tech-container"
      aria-hidden="true"
    >
      <canvas ref={canvasRef} className="landing-ambient-tech-canvas" />
    </div>
  );
}

export default memo(LandingAmbientTech);
