import { useEffect, useState, useCallback } from 'react';

export function useInView(threshold = 0.15) {
  const [element, setElement] = useState<HTMLDivElement | null>(null);
  const [isInView, setIsInView] = useState(false);

  const ref = useCallback((node: HTMLDivElement | null) => {
    if (node) setElement(node);
  }, []);

  useEffect(() => {
    if (!element || isInView) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { threshold }
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, [element, isInView, threshold]);

  return { ref, isInView };
}
