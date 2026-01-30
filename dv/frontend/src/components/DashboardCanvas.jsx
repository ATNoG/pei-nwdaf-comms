/**
 * Main canvas component with ReactFlow visualization.
 */
import React, { useCallback, useRef, useMemo, useState, useEffect } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Connection,
} from 'reactflow';
import 'reactflow/dist/style.css';

import ContainerNode from './ContainerNode';
import ImageNode from './ImageNode';
import FrameNode from './FrameNode';
import { pendingUpdatesRef } from '../hooks/useDashboardState';
import apiService from '../services/api';

const nodeTypes = {
  container: ContainerNode,
  image: ImageNode,
  frame: FrameNode,
};

const DashboardCanvas = ({
  dashboardState,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onNodeClick,
  onEdgeClick,
  onPaneClick,
  onNodeDragStop,
  onEditBox,
  onEditImage,
  onEditFrame,
  clickThroughMode,
}) => {
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [initialized, setInitialized] = useState(false);
  const prevBoxesRef = useRef(null);

  // Convert boxes, images, and frames to React Flow nodes
  const nodes = useMemo(() => {
    if (!dashboardState) {
      return [];
    }

    const frameNodes = (dashboardState.frames || []).map((frame) => ({
      id: frame.id,
      type: 'frame',
      position: { x: frame.x, y: frame.y },
      draggable: !dashboardState.locked,
      data: {
        ...frame,
        locked: dashboardState.locked,
        onEdit: onEditFrame,
      },
      style: {
        width: frame.width,
        height: frame.height,
      },
      // Always render frames first (at the bottom)
      zIndex: -1,
    }));

    const boxNodes = (dashboardState.boxes || []).map((box) => ({
      id: box.id,
      type: 'container',
      position: { x: box.x, y: box.y },
      draggable: !dashboardState.locked,
      data: {
        ...box,
        locked: dashboardState.locked,
        onEdit: onEditBox,
      },
      zIndex: 100,
    }));

    const imageNodes = (dashboardState.images || []).map((image) => ({
      id: image.id,
      type: 'image',
      position: { x: image.x, y: image.y },
      draggable: !dashboardState.locked,
      data: {
        ...image,
        locked: dashboardState.locked,
        onEdit: onEditImage,
        clickThroughMode,
      },
      style: {
        width: image.width,
        height: image.height,
      },
      zIndex: image.layer_type === 'background' ? 0 : 1000,
    }));

    // Background images first, then boxes, then foreground images
    const backgroundImages = imageNodes.filter(n => n.data.layer_type === 'background');
    const foregroundImages = imageNodes.filter(n => n.data.layer_type === 'foreground');

    // Order: frames first (bottom), then background images, then foreground images, then boxes (top for clicks)
    // Boxes are last so they receive clicks first, but z-index makes images appear on top visually
    return [...frameNodes, ...backgroundImages, ...foregroundImages, ...boxNodes];
  }, [dashboardState?.boxes, dashboardState?.images, dashboardState?.frames, dashboardState?.locked, onEditBox, onEditImage, onEditFrame]);

  // Convert lines to React Flow edges
  const edges = useMemo(() => {
    if (!dashboardState || !dashboardState.lines) {
      return [];
    }
    return dashboardState.lines.map((line) => {
      // Handle free lines (not connected to boxes)
      if (line.source_box_id === 'free_start' && line.target_box_id === 'free_end') {
        return {
          id: line.id,
          source: line.id,
          target: line.id,
          type: 'straight',
          data: { isFreeLine: true, ...line },
          style: {
            stroke: line.status === 'nok' && line.red_on_failure ? '#ff0000' : line.color || '#000000',
            strokeWidth: 2,
          },
        };
      }

      // Regular box-to-box connections
      return {
        id: line.id,
        source: line.source_box_id,
        target: line.target_box_id,
        type: 'smoothstep',
        data: line,
        style: {
          stroke: line.status === 'nok' && line.red_on_failure ? '#ff0000' : line.color || '#000000',
          strokeWidth: 2,
        },
      };
    });
  }, [dashboardState?.lines]);

  const [internalNodes, setInternalNodes, onInternalNodesChange] = useNodesState([]);
  const [internalEdges, setInternalEdges, onInternalEdgesChange] = useEdgesState([]);

  // Initialize nodes and edges once
  useEffect(() => {
    if (!initialized && nodes.length > 0) {
      setInternalNodes(nodes);
      setInternalEdges(edges);
      setInitialized(true);
      prevBoxesRef.current = JSON.parse(JSON.stringify(dashboardState?.boxes || [])); // Deep copy
    }
  }, [initialized, nodes, edges, setInternalNodes, setInternalEdges, dashboardState?.boxes]);

  // Update node data without changing positions - handle both pending and non-pending
  useEffect(() => {
    if (initialized) {
      const pendingIds = pendingUpdatesRef.current;

      setInternalNodes((currentNodes) => {
        // Map current frames to nodes
        const frameNodes = (dashboardState.frames || []).map((frame) => {
          const existingNode = currentNodes.find(n => n.id === frame.id);

          // If this node is pending (being dragged), preserve its position
          if (existingNode && pendingIds.has(frame.id)) {
            return existingNode;
          }

          // Otherwise, create/update node from frame data
          return {
            id: frame.id,
            type: 'frame',
            position: { x: frame.x, y: frame.y },
            draggable: !dashboardState.locked,
            data: {
              ...frame,
              locked: dashboardState.locked,
              onEdit: onEditFrame,
            },
            style: {
              width: frame.width,
              height: frame.height,
            },
            zIndex: -1,
          };
        });

        // Map current boxes to nodes
        const boxNodes = dashboardState.boxes.map((box) => {
          const existingNode = currentNodes.find(n => n.id === box.id);

          // If this node is pending (being dragged/resized), preserve ALL its properties
          if (existingNode && pendingIds.has(box.id)) {
            return existingNode;
          }

          // Otherwise, create/update node from box data
          return {
            id: box.id,
            type: 'container',
            position: { x: box.x, y: box.y },
            draggable: !dashboardState.locked,
            data: {
              ...box,
              locked: dashboardState.locked,
              onEdit: onEditBox,
            },
            zIndex: 100,
          };
        });

        // Map current images to nodes
        const imageNodes = dashboardState.images.map((image) => {
          const existingNode = currentNodes.find(n => n.id === image.id);

          // If this node is pending (being dragged), preserve its position
          if (existingNode && pendingIds.has(image.id)) {
            return existingNode;
          }

          // Otherwise, create/update node from image data
          return {
            id: image.id,
            type: 'image',
            position: { x: image.x, y: image.y },
            draggable: !dashboardState.locked,
            data: {
              ...image,
              locked: dashboardState.locked,
              onEdit: onEditImage,
              clickThroughMode,
            },
            style: {
              width: image.width,
              height: image.height,
            },
            zIndex: image.layer_type === 'background' ? 0 : 1000,
          };
        });

        // Background images first, then boxes, then foreground images
        const backgroundImages = imageNodes.filter(n => n.data.layer_type === 'background');
        const foregroundImages = imageNodes.filter(n => n.data.layer_type === 'foreground');

        // Order: frames first (bottom), then background images, then foreground images, then boxes (top for clicks)
        // Boxes are last so they receive clicks first, but z-index makes images appear on top visually
        return [...frameNodes, ...backgroundImages, ...foregroundImages, ...boxNodes];
      });
    }
  }, [dashboardState?.boxes, dashboardState?.images, dashboardState?.frames, dashboardState?.locked, initialized, onEditBox, onEditImage, onEditFrame, setInternalNodes]);

  // Update edges when they change
  useEffect(() => {
    if (initialized) {
      setInternalEdges(edges);
    }
  }, [edges, initialized, setInternalEdges]);

  // Resize state - must be after useNodesState
  const [isResizing, setIsResizing] = useState(false);
  const resizeStartPos = useRef(null);
  const resizeStartSize = useRef(null);
  const resizingNodeId = useRef(null);

  // Handle node drag start - check if clicking resize handle
  const handleNodeDragStart = useCallback((event, node) => {
    // Check if the click target is a resize handle
    if (event.target instanceof Element && event.target.closest('[data-resize-handle="true"]')) {
      event.preventDefault();
      setIsResizing(true);
      resizingNodeId.current = node.id;
      resizeStartPos.current = { x: event.clientX, y: event.clientY };
      resizeStartSize.current = { width: node.data.width || 200, height: node.data.height || 150 };
      // Add to pending updates so state sync won't overwrite resize
      pendingUpdatesRef.current.add(node.id);
      return false; // Prevent drag
    }
  }, []);

  // Handle node drag for resizing
  const handleNodeDrag = useCallback((event, node) => {
    if (!isResizing || !resizeStartPos.current || !resizeStartSize.current) return;

    const dx = event.clientX - resizeStartPos.current.x;
    const dy = event.clientY - resizeStartPos.current.y;

    const newWidth = Math.max(
      node.type === 'image' ? 50 : node.type === 'frame' ? 100 : 150,
      resizeStartSize.current.width + dx
    );
    const newHeight = Math.max(
      node.type === 'image' ? 50 : node.type === 'frame' ? 100 : 100,
      resizeStartSize.current.height + dy
    );

    setInternalNodes(nodes => nodes.map(n => {
      if (n.id === resizingNodeId.current) {
        return {
          ...n,
          style: { width: newWidth, height: newHeight },
          data: { ...n.data, width: newWidth, height: newHeight }
        };
      }
      return n;
    }));
  }, [isResizing, setInternalNodes]);

  // Handle node drag end - finish resize or save position
  const handleNodeDragEndWrapper = useCallback(async (event, node) => {
    if (isResizing && resizingNodeId.current) {
      // Finish resize - make direct API call
      const resizedNode = internalNodes.find(n => n.id === resizingNodeId.current);
      if (resizedNode) {
        try {
          if (resizedNode.type === 'image') {
            await apiService.updateImage(resizedNode.id, {
              id: resizedNode.id,
              name: resizedNode.data.name,
              layer_type: resizedNode.data.layer_type,
              url: resizedNode.data.url,
              x: resizedNode.position.x,
              y: resizedNode.position.y,
              width: resizedNode.data.width,
              height: resizedNode.data.height,
            });
          } else if (resizedNode.type === 'frame') {
            // Frame
            const frameData = resizedNode.data;
            await apiService.updateFrame(resizedNode.id, {
              id: frameData.id,
              name: frameData.name,
              x: resizedNode.position.x,
              y: resizedNode.position.y,
              width: frameData.width,
              height: frameData.height,
              border_color: frameData.border_color,
              border_width: frameData.border_width,
              border_style: frameData.border_style,
            });
          } else {
            // Box
            const boxData = resizedNode.data;
            await apiService.updateBox(resizedNode.id, {
              id: boxData.id,
              name: boxData.name,
              x: boxData.x,
              y: boxData.y,
              status_url: boxData.status_url || null,
              parameters: boxData.parameters || {},
              attributes: boxData.attributes || [],
              expanded: boxData.expanded || false,
              visible_on_map: boxData.visible_on_map || [],
              width: boxData.width || 200,
              height: boxData.height || 150,
            });
          }
        } catch (err) {
          console.error('Failed to save resize:', err);
        } finally {
          // Remove from pending updates after a delay to allow WebSocket updates to propagate
          setTimeout(() => {
            pendingUpdatesRef.current.delete(resizingNodeId.current);
          }, 2000);
        }
      }
      setIsResizing(false);
      resizingNodeId.current = null;
      resizeStartPos.current = null;
      resizeStartSize.current = null;
    } else {
      // Normal drag stop - save position
      onNodeDragStop(event, node);
    }
  }, [isResizing, internalNodes, onNodeDragStop]);

  // Listen to mouse move for resize
  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e) => {
      if (!resizeStartPos.current || !resizeStartSize.current) return;

      const dx = e.clientX - resizeStartPos.current.x;
      const dy = e.clientY - resizeStartPos.current.y;

      setInternalNodes(nodes => {
        return nodes.map(n => {
          if (n.id === resizingNodeId.current) {
            const newWidth = Math.max(
              n.type === 'image' ? 50 : n.type === 'frame' ? 100 : 150,
              resizeStartSize.current.width + dx
            );
            const newHeight = Math.max(
              n.type === 'image' ? 50 : n.type === 'frame' ? 100 : 100,
              resizeStartSize.current.height + dy
            );

            return {
              ...n,
              style: { width: newWidth, height: newHeight },
              data: { ...n.data, width: newWidth, height: newHeight }
            };
          }
          return n;
        });
      });
    };

    const handleMouseUp = async () => {
      const resizedNode = internalNodes.find(n => n.id === resizingNodeId.current);
      if (resizedNode) {
        try {
          if (resizedNode.type === 'image') {
            await apiService.updateImage(resizedNode.id, {
              id: resizedNode.id,
              name: resizedNode.data.name,
              layer_type: resizedNode.data.layer_type,
              url: resizedNode.data.url,
              x: resizedNode.position.x,
              y: resizedNode.position.y,
              width: resizedNode.data.width,
              height: resizedNode.data.height,
            });
          } else if (resizedNode.type === 'frame') {
            // Frame
            const frameData = resizedNode.data;
            await apiService.updateFrame(resizedNode.id, {
              id: frameData.id,
              name: frameData.name,
              x: resizedNode.position.x,
              y: resizedNode.position.y,
              width: frameData.width,
              height: frameData.height,
              border_color: frameData.border_color,
              border_width: frameData.border_width,
              border_style: frameData.border_style,
            });
          } else {
            // Box
            const boxData = resizedNode.data;
            await apiService.updateBox(resizedNode.id, {
              id: boxData.id,
              name: boxData.name,
              x: boxData.x,
              y: boxData.y,
              status_url: boxData.status_url || null,
              parameters: boxData.parameters || {},
              attributes: boxData.attributes || [],
              expanded: boxData.expanded || false,
              visible_on_map: boxData.visible_on_map || [],
              width: boxData.width || 200,
              height: boxData.height || 150,
            });
          }
        } catch (err) {
          console.error('Failed to save resize:', err);
        } finally {
          // Remove from pending updates after a delay to allow WebSocket updates to propagate
          setTimeout(() => {
            pendingUpdatesRef.current.delete(resizingNodeId.current);
          }, 2000);
        }
      }
      setIsResizing(false);
      resizingNodeId.current = null;
      resizeStartPos.current = null;
      resizeStartSize.current = null;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, internalNodes, setInternalNodes]);

  const onLoad = useCallback((rf) => {
    setReactFlowInstance(rf);
  }, []);

  return (
    <div className="h-full" ref={reactFlowWrapper}>
      <ReactFlow
        nodes={internalNodes}
        edges={internalEdges}
        onNodesChange={(changes) => {
          onInternalNodesChange(changes);
          onNodesChange?.(changes);
        }}
        onEdgesChange={(changes) => {
          onInternalEdgesChange(changes);
          onEdgesChange?.(changes);
        }}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onPaneClick={onPaneClick}
        onNodeDragStart={handleNodeDragStart}
        onNodeDrag={handleNodeDrag}
        onNodeDragStop={handleNodeDragEndWrapper}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
        onLoad={onLoad}
      >
        <Background color="#aaa" gap={16} />
        <Controls />
        <MiniMap
          style={{
            height: 120,
            backgroundColor: '#f8f8f8',
          }}
          zoomable
          pannable
        />
      </ReactFlow>
    </div>
  );
};

export default DashboardCanvas;
