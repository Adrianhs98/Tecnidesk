import { useState, useEffect, useRef, useCallback } from "react";

/**
 * Hook to detect when an element enters or leaves the viewport.
 * Uses native IntersectionObserver with safe fallback for test/SSR environments.
 *
 * @param {Object} options
 * @param {number|number[]} [options.threshold=0.15]
 * @param {string} [options.rootMargin="0px"]
 * @param {boolean} [options.once=false]
 * @returns {[React.RefObject, boolean]} [ref, isInView]
 */
export function useInView(options = {}) {
  const { threshold = 0.15, rootMargin = "0px", once = false } = options;
  const ref = useRef(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    if (typeof window === "undefined" || !("IntersectionObserver" in window)) {
      setIsInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        const isIntersecting = entry.isIntersecting;
        if (isIntersecting) {
          setIsInView(true);
          if (once) {
            observer.unobserve(el);
          }
        } else if (!once) {
          setIsInView(false);
        }
      },
      { threshold, rootMargin }
    );

    observer.observe(el);

    return () => {
      observer.disconnect();
    };
  }, [threshold, rootMargin, once]);

  return [ref, isInView];
}

/**
 * Hook to compute normalized scroll progress [0, 1] through a tall track element.
 *
 * Performance-optimized:
 * - Uses IntersectionObserver to detect when the track is in or near the viewport.
 * - ONLY attaches a passive scroll listener while the track is intersecting.
 * - Batches calculations to a single requestAnimationFrame per scroll tick.
 * - Automatically halts all work when out of view.
 * - Safely cleans up on unmount.
 *
 * @param {React.RefObject} trackRef - Ref to the tall track container.
 * @param {Object} [options]
 * @param {number} [options.stickyOffset=88] - Offset in pixels (e.g. navbar height + gap).
 * @param {function} [options.onProgress] - Optional callback receiving (progress, raw).
 * @returns {number} progress between 0 and 1.
 */
export function useScrollProgress(trackRef, options = {}) {
  const { stickyOffset = 88, onProgress } = options;
  const [progress, setProgress] = useState(0);
  const progressRef = useRef(0);
  const isIntersectingRef = useRef(false);
  const rafIdRef = useRef(null);

  const calculate = useCallback(() => {
    const el = trackRef.current;
    if (!el) return;

    const rect = el.getBoundingClientRect();
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;

    // Total distance the top of the track travels from when it hits stickyOffset
    // until the bottom of the track aligns with the bottom of the sticky window.
    const scrollableDistance = rect.height - (viewportHeight - stickyOffset);

    if (scrollableDistance <= 0) {
      setProgress(0);
      progressRef.current = 0;
      if (onProgress) onProgress(0);
      return;
    }

    // Distance scrolled past the sticky point
    const scrolled = stickyOffset - rect.top;
    const rawRatio = scrolled / scrollableDistance;
    const clamped = Math.max(0, Math.min(1, rawRatio));

    // Only update state if difference is meaningful (> 0.005) to prevent redundant re-renders
    if (Math.abs(clamped - progressRef.current) >= 0.005 || clamped === 0 || clamped === 1) {
      progressRef.current = clamped;
      setProgress(clamped);
      if (onProgress) onProgress(clamped);
    }
  }, [stickyOffset, trackRef, onProgress]);

  useEffect(() => {
    const el = trackRef.current;
    if (!el) return;

    if (typeof window === "undefined" || !("IntersectionObserver" in window)) {
      return;
    }

    const handleScroll = () => {
      if (!isIntersectingRef.current) return;
      if (rafIdRef.current === null) {
        rafIdRef.current = requestAnimationFrame(() => {
          calculate();
          rafIdRef.current = null;
        });
      }
    };

    const observer = new IntersectionObserver(
      ([entry]) => {
        isIntersectingRef.current = entry.isIntersecting;
        if (entry.isIntersecting) {
          calculate();
          window.addEventListener("scroll", handleScroll, { passive: true });
          window.addEventListener("resize", handleScroll, { passive: true });
        } else {
          window.removeEventListener("scroll", handleScroll);
          window.removeEventListener("resize", handleScroll);
          if (rafIdRef.current !== null) {
            cancelAnimationFrame(rafIdRef.current);
            rafIdRef.current = null;
          }
        }
      },
      {
        // Add vertical margin so calculations start just before entering
        rootMargin: "100px 0px 100px 0px",
        threshold: 0,
      }
    );

    observer.observe(el);

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleScroll);
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
    };
  }, [trackRef, calculate]);

  return progress;
}
