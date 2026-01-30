/**
 * Custom hook for managing dashboard state.
 * Status polling is now handled by the backend.
 */
import { useState, useEffect, useCallback } from 'react';
import apiService from '../services/api';
import useWebSocket from './useWebSocket';
import { useToast } from './useToast';

// Default state to prevent undefined errors
const DEFAULT_STATE = {
  boxes: [],
  lines: [],
  images: [],
  frames: [],
  locked: false,
  zoom: 1.0,
  pan_x: 0,
  pan_y: 0,
};

// Global ref to track boxes with pending updates (shared across components)
export const pendingUpdatesRef = { current: new Set() };

const useDashboardState = () => {
  const [dashboardState, setDashboardState] = useState(DEFAULT_STATE);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { error: showError } = useToast();

  // Load initial state
  const loadState = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const state = await apiService.getState();
      // Ensure all properties exist
      setDashboardState({
        boxes: state?.boxes || [],
        lines: state?.lines || [],
        images: state?.images || [],
        frames: state?.frames || [],
        locked: state?.locked || false,
        zoom: state?.zoom || 1.0,
        pan_x: state?.pan_x || 0,
        pan_y: state?.pan_y || 0,
      });
    } catch (err) {
      setError(err.message);
      showError(`Failed to load dashboard: ${err.message}`);
      // Set default state on error
      setDashboardState(DEFAULT_STATE);
    } finally {
      setLoading(false);
    }
  }, [showError]);

  // Handle WebSocket messages - intelligently merge updates
  const handleWebSocketMessage = useCallback((message) => {
    if (message.type === 'state_update' && message.data) {
      const incomingBoxes = message.data?.boxes || [];
      const incomingBoxIds = new Set(incomingBoxes.map(b => b.id));
      const pendingIds = pendingUpdatesRef.current;

      setDashboardState((prev) => {
        // 1. Keep boxes that are pending updates (local edits in progress)
        const pendingBoxes = prev.boxes.filter(b => pendingIds.has(b.id));

        // 2. Update non-pending boxes with incoming data, filter out deleted ones
        const updatedBoxes = prev.boxes
          .filter(b => !pendingIds.has(b.id))
          .map(existingBox => {
            const incomingBox = incomingBoxes.find(b => b.id === existingBox.id);
            return incomingBox || null; // null means deleted
          })
          .filter(Boolean);

        // 3. Add new boxes from server
        const existingLocalIds = new Set([...pendingBoxes, ...updatedBoxes].map(b => b.id));
        const newBoxes = incomingBoxes.filter(b => !existingLocalIds.has(b.id));

        return {
          boxes: [...pendingBoxes, ...updatedBoxes, ...newBoxes],
          lines: message.data?.lines || prev.lines || [],
          images: message.data?.images || prev.images || [],
          frames: message.data?.frames || prev.frames || [],
          locked: message.data?.locked ?? prev.locked,
          zoom: message.data?.zoom ?? prev.zoom,
          pan_x: message.data?.pan_x ?? prev.pan_x,
          pan_y: message.data?.pan_y ?? prev.pan_y,
        };
      });
    }
  }, []);

  // Setup WebSocket connection
  useWebSocket(handleWebSocketMessage, true);

  // Initial load
  useEffect(() => {
    loadState();
  }, [loadState]);

  return {
    dashboardState,
    setDashboardState,
    loading,
    error,
    reload: loadState,
  };
};

export default useDashboardState;
