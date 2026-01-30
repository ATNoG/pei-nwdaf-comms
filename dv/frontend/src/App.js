/**
 * Main application component.
 * Orchestrates the dashboard visualization and user interactions.
 */
import React, { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';

import useDashboardState, { pendingUpdatesRef } from './hooks/useDashboardState';
import { ToastProvider, ToastContainer, useToast } from './hooks/useToast';

import Header from './components/Header';
import DashboardCanvas from './components/DashboardCanvas';
import AddBoxModal from './components/AddBoxModal';
import AddImageModal from './components/AddImageModal';
import AddFrameModal from './components/AddFrameModal';
import EditBoxModal from './components/EditBoxModal';

import apiService from './services/api';

import './App.css';

function AppContent() {
  const { success, error } = useToast();
  const { dashboardState, setDashboardState, loading, error: stateError, reload } = useDashboardState();

  const [selectedItem, setSelectedItem] = useState(null);
  const [showAddBoxModal, setShowAddBoxModal] = useState(false);
  const [showAddImageModal, setShowAddImageModal] = useState(false);
  const [showAddFrameModal, setShowAddFrameModal] = useState(false);
  const [showEditBoxModal, setShowEditBoxModal] = useState(false);
  const [editingBox, setEditingBox] = useState(null);
  const [clickThroughMode, setClickThroughMode] = useState(false);

  // Toggle click-through mode
  const handleToggleClickThrough = useCallback(() => {
    setClickThroughMode(prev => {
      const newValue = !prev;
      setSelectedItem(null); // Clear selection when toggling
      return newValue;
    });
  }, []);

  // Handle node selection
  const handleNodeClick = useCallback((event, node) => {
    // In click-through mode, ignore image clicks - let them pass through to boxes
    if (clickThroughMode && node.type === 'image') {
      return;
    }

    const nodeType = node.type === 'image' ? 'image' : node.type === 'frame' ? 'frame' : 'box';
    if (selectedItem && selectedItem.type === nodeType && selectedItem.id === node.id) {
      setSelectedItem(null);
    } else {
      setSelectedItem({ type: nodeType, id: node.id });
    }
  }, [selectedItem, clickThroughMode]);

  // Handle edge selection
  const handleEdgeClick = useCallback((event, edge) => {
    if (selectedItem && selectedItem.type === 'line' && selectedItem.id === edge.id) {
      setSelectedItem(null);
    } else {
      setSelectedItem({ type: 'line', id: edge.id });
    }
  }, [selectedItem]);

  // Handle pane click for deselection
  const handlePaneClick = useCallback(() => {
    setSelectedItem(null);
  }, []);

  // Handle connection between nodes
  const handleConnect = useCallback(async (params) => {
    try {
      const newLine = {
        id: uuidv4(),
        source_box_id: params.source,
        target_box_id: params.target,
        color: '#000000',
        polling_interval: 2,
        change_on_response: false,
        red_on_failure: false,
      };

      await apiService.createLine(newLine);
      success('Connection created');
    } catch (err) {
      error(`Failed to create connection: ${err.message}`);
    }
  }, [success, error]);

  // Handle node position updates - uses global pendingUpdatesRef
  const handleNodeDragStop = useCallback(async (event, node) => {
    const box = dashboardState.boxes?.find((b) => b.id === node.id);
    const image = dashboardState.images?.find((i) => i.id === node.id);
    const frame = dashboardState.frames?.find((f) => f.id === node.id);

    if (box) {
      // Mark this box as having a pending update (uses global ref)
      pendingUpdatesRef.current.add(node.id);

      try {
        // Only send the fields that changed - don't send position object
        const updatedBox = {
          id: box.id,
          name: box.name,
          x: node.position.x,
          y: node.position.y,
          status_url: box.status_url || null,
          parameters: box.parameters || {},
          attributes: box.attributes || [],
          expanded: box.expanded || false,
          visible_on_map: box.visible_on_map || [],
          width: box.width || 200,
          height: box.height || 150,
        };
        await apiService.updateBox(node.id, updatedBox);
      } catch (err) {
        error(`Failed to update box position: ${err.message}`);
      } finally {
        // Remove pending flag after a delay to allow all WebSocket updates to propagate
        setTimeout(() => {
          pendingUpdatesRef.current.delete(node.id);
        }, 2000);
      }
    } else if (image) {
      // Handle image drag
      pendingUpdatesRef.current.add(node.id);

      try {
        const updatedImage = {
          id: image.id,
          name: image.name,
          layer_type: image.layer_type,
          url: image.url,
          x: node.position.x,
          y: node.position.y,
          width: image.width,
          height: image.height,
        };
        await apiService.updateImage(node.id, updatedImage);
      } catch (err) {
        error(`Failed to update image position: ${err.message}`);
      } finally {
        setTimeout(() => {
          pendingUpdatesRef.current.delete(node.id);
        }, 2000);
      }
    } else if (frame) {
      // Handle frame drag
      pendingUpdatesRef.current.add(node.id);

      try {
        const updatedFrame = {
          id: frame.id,
          name: frame.name,
          x: node.position.x,
          y: node.position.y,
          width: frame.width,
          height: frame.height,
          border_color: frame.border_color,
          border_width: frame.border_width,
          border_style: frame.border_style,
        };
        await apiService.updateFrame(node.id, updatedFrame);
      } catch (err) {
        error(`Failed to update frame position: ${err.message}`);
      } finally {
        setTimeout(() => {
          pendingUpdatesRef.current.delete(node.id);
        }, 2000);
      }
    }
  }, [dashboardState.boxes, dashboardState.images, dashboardState.frames, error]);

  // Toggle lock mode
  const handleToggleLock = useCallback(async () => {
    try {
      await apiService.toggleLock();
    } catch (err) {
      error(`Failed to toggle lock: ${err.message}`);
    }
  }, [error]);

  // Delete selected item
  const handleDeleteSelected = useCallback(async () => {
    if (!selectedItem) return;

    // Optimistic update - remove from local state immediately
    if (selectedItem.type === 'box') {
      setDashboardState((prev) => ({
        ...prev,
        boxes: prev.boxes.filter(b => b.id !== selectedItem.id),
      }));
    } else if (selectedItem.type === 'line') {
      setDashboardState((prev) => ({
        ...prev,
        lines: prev.lines.filter(l => l.id !== selectedItem.id),
      }));
    } else if (selectedItem.type === 'image') {
      setDashboardState((prev) => ({
        ...prev,
        images: prev.images.filter(i => i.id !== selectedItem.id),
      }));
    } else if (selectedItem.type === 'frame') {
      setDashboardState((prev) => ({
        ...prev,
        frames: prev.frames.filter(f => f.id !== selectedItem.id),
      }));
    }

    try {
      if (selectedItem.type === 'box') {
        await apiService.deleteBox(selectedItem.id);
        success('Box deleted');
      } else if (selectedItem.type === 'line') {
        await apiService.deleteLine(selectedItem.id);
        success('Connection deleted');
      } else if (selectedItem.type === 'image') {
        await apiService.deleteImage(selectedItem.id);
        success('Image deleted');
      } else if (selectedItem.type === 'frame') {
        await apiService.deleteFrame(selectedItem.id);
        success('Frame deleted');
      }
      setSelectedItem(null);
    } catch (err) {
      error(`Failed to delete item: ${err.message}`);
      // Reload state to fix any inconsistency
      reload();
    }
  }, [selectedItem, success, error, setDashboardState, reload]);

  // Handle edit selected
  const handleEditSelected = useCallback(() => {
    if (selectedItem?.type === 'box') {
      const box = dashboardState.boxes.find((b) => b.id === selectedItem.id);
      if (box) {
        setEditingBox({ ...box });
        setShowEditBoxModal(true);
      }
    }
  }, [selectedItem, dashboardState.boxes]);

  // Handle box updated
  const handleBoxUpdated = useCallback((box) => {
    // Update local state
    setDashboardState((prev) => ({
      ...prev,
      boxes: prev.boxes.map((b) =>
        b.id === box.id ? { ...box } : b
      ),
    }));

    setShowEditBoxModal(false);
    setEditingBox(null);
  }, []);

  // Handle box added
  const handleBoxAdded = useCallback(() => {
    setShowAddBoxModal(false);
  }, []);

  // Handle image added
  const handleImageAdded = useCallback(() => {
    setShowAddImageModal(false);
  }, []);

  // Handle frame added
  const handleFrameAdded = useCallback(() => {
    setShowAddFrameModal(false);
  }, []);

  // Handle edit button click from node
  const handleEditBox = useCallback((boxId) => {
    const box = dashboardState.boxes.find((b) => b.id === boxId);
    if (box) {
      setEditingBox({ ...box });
      setShowEditBoxModal(true);
    }
  }, [dashboardState.boxes]);

  // Handle image inline edit
  const handleEditImage = useCallback(async (imageId, updatedData) => {
    try {
      await apiService.updateImage(imageId, updatedData);
      // State will update via WebSocket
    } catch (err) {
      error(`Failed to update image: ${err.message}`);
    }
  }, [error]);

  // Handle frame inline edit
  const handleEditFrame = useCallback(async (frameId, updatedData) => {
    try {
      await apiService.updateFrame(frameId, updatedData);
      // State will update via WebSocket
    } catch (err) {
      error(`Failed to update frame: ${err.message}`);
    }
  }, [error]);

  // Show loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (stateError) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="text-center bg-white p-8 rounded-lg shadow-lg">
          <h2 className="text-xl font-bold text-red-600 mb-2">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">{stateError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <Header
        locked={dashboardState.locked}
        onToggleLock={handleToggleLock}
        onAddBox={() => setShowAddBoxModal(true)}
        onAddImage={() => setShowAddImageModal(true)}
        onAddFrame={() => setShowAddFrameModal(true)}
        selectedItem={selectedItem}
        onEditSelected={handleEditSelected}
        onDeleteSelected={handleDeleteSelected}
        clickThroughMode={clickThroughMode}
        onToggleClickThrough={handleToggleClickThrough}
      />

      <main className="flex-1 overflow-hidden relative">
        <DashboardCanvas
          dashboardState={dashboardState}
          onConnect={handleConnect}
          onNodeClick={handleNodeClick}
          onEdgeClick={handleEdgeClick}
          onPaneClick={handlePaneClick}
          onNodeDragStop={handleNodeDragStop}
          onEditBox={handleEditBox}
          onEditImage={handleEditImage}
          onEditFrame={handleEditFrame}
          clickThroughMode={clickThroughMode}
        />
      </main>

      <AddBoxModal
        show={showAddBoxModal}
        onClose={() => setShowAddBoxModal(false)}
        onBoxAdded={handleBoxAdded}
      />

      <AddImageModal
        show={showAddImageModal}
        onClose={() => setShowAddImageModal(false)}
        onImageAdded={handleImageAdded}
      />

      <AddFrameModal
        show={showAddFrameModal}
        onClose={() => setShowAddFrameModal(false)}
        onFrameAdded={handleFrameAdded}
      />

      <EditBoxModal
        show={showEditBoxModal}
        box={editingBox}
        onClose={() => {
          setShowEditBoxModal(false);
          setEditingBox(null);
        }}
        onBoxUpdated={handleBoxUpdated}
      />

      <ToastContainer />
    </div>
  );
}

function App() {
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  );
}

export default App;
