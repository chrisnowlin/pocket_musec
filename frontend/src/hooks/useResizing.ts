import { useState, useEffect, MouseEvent as ReactMouseEvent } from 'react';
import type { PanelSide } from '../types/unified';

export function useResizing(initialSidebarWidth: number, initialRightPanelWidth: number) {
  const [sidebarWidth, setSidebarWidth] = useState(initialSidebarWidth);
  const [rightPanelWidth, setRightPanelWidth] = useState(initialRightPanelWidth);
  const [resizingPanel, setResizingPanel] = useState<PanelSide | null>(null);
  const [startX, setStartX] = useState(0);
  const [startWidth, setStartWidth] = useState(0);

  const handleResizerMouseDown = (panel: PanelSide, event: ReactMouseEvent<HTMLDivElement>) => {
    setResizingPanel(panel);
    setStartX(event.clientX);
    setStartWidth(panel === 'sidebar' ? sidebarWidth : rightPanelWidth);
    event.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      if (resizingPanel) {
        if (resizingPanel === 'sidebar') {
          const delta = event.clientX - startX;
          const width = Math.min(Math.max(startWidth + delta, 200), 400);
          setSidebarWidth(width);
        } else if (resizingPanel === 'right') {
          const delta = event.clientX - startX;
          const width = Math.min(Math.max(startWidth - delta, 300), 600);
          setRightPanelWidth(width);
        }
      }
    };

    const handleMouseUp = () => {
      setResizingPanel(null);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [resizingPanel, startX, startWidth]);

  useEffect(() => {
    document.body.classList.toggle('no-select', Boolean(resizingPanel));
  }, [resizingPanel]);

  return {
    sidebarWidth,
    rightPanelWidth,
    resizingPanel,
    handleResizerMouseDown,
  };
}

export function useMessageContainerResizing(initialHeight: number | null) {
  const [messageContainerHeight, setMessageContainerHeight] = useState<number | null>(
    initialHeight
  );
  const [resizing, setResizing] = useState(false);
  const [startY, setStartY] = useState(0);
  const [startHeight, setStartHeight] = useState(0);

  const handleResizerMouseDown = (
    event: ReactMouseEvent<HTMLDivElement>,
    containerRef: React.RefObject<HTMLDivElement>
  ) => {
    setResizing(true);
    setStartY(event.clientY);
    setStartHeight(messageContainerHeight || (containerRef.current?.offsetHeight ?? 400));
    event.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      if (resizing) {
        const delta = event.clientY - startY;
        const height = Math.min(Math.max(startHeight - delta, 200), window.innerHeight - 300);
        setMessageContainerHeight(height);
      }
    };

    const handleMouseUp = () => {
      setResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [resizing, startY, startHeight]);

  useEffect(() => {
    document.body.classList.toggle('no-select', resizing);
  }, [resizing]);

  return {
    messageContainerHeight,
    resizing,
    handleResizerMouseDown,
  };
}
