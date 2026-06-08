import { useState, useEffect } from 'react';

/**
 * Custom hook to detect screen size breakpoints
 * Returns: { isMobile, isTablet, isDesktop, width }
 */
export function useResponsive() {
  const [width, setWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1200);

  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return {
    isMobile: width <= 768,
    isSmallMobile: width <= 480,
    isTablet: width > 768 && width <= 1024,
    isDesktop: width > 1024,
    width
  };
}
