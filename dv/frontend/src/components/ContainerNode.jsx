/**
 * Custom React Flow node component for Docker containers.
 * Displays container name, status indicator, and attributes.
 *
 * Attributes can be:
 * - ok_nok: Shows a colored dot (green for OK, yellow for 4xx, red for 5xx)
 * - text: Shows a truncated text preview with a button to view full content
 */
import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { Handle, Position } from 'reactflow';
import { Settings, ExternalLink, Maximize2 } from 'lucide-react';

// Text modal component (will be rendered outside ReactFlow)
const TextModal = ({ attr, onClose }) => {
  if (!attr) return null;

  const content = attr.statusInfo?.value || attr.statusInfo?.text || 'No content';

  return createPortal(
    <div className="text-modal-overlay" onClick={onClose}>
      <div className="text-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="text-modal-header">
          <h4>{attr.label || attr.name}</h4>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="text-modal-body">
          <div className="text-content-scrollable">
            <pre>{content}</pre>
          </div>
          {attr.url && (
            <a
              href={attr.url}
              target="_blank"
              rel="noopener noreferrer"
              className="external-link"
            >
              <ExternalLink size={14} />
              Open URL
            </a>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
};

const ContainerNode = ({ data, selected }) => {
  const [showFullText, setShowFullText] = useState(null);

  const getStatusColor = (statusInfo) => {
    if (!statusInfo) return '#9ca3af'; // gray for unknown

    const { status, value } = statusInfo;

    // Check if value is an HTTP status code
    const httpStatus = typeof value === 'number' ? value : parseInt(value);

    if (!isNaN(httpStatus)) {
      if (httpStatus >= 200 && httpStatus < 300) return '#10b981'; // green
      if (httpStatus >= 400 && httpStatus < 500) return '#f59e0b'; // yellow
      if (httpStatus >= 500) return '#ef4444'; // red
    }

    // Status string
    if (status === 'ok') return '#10b981'; // green
    if (status === 'warning') return '#f59e0b'; // yellow
    if (status === 'nok') return '#ef4444'; // red
    return '#9ca3af'; // gray
  };

  const getAttributeStatusColor = (attr) => {
    if (!attr.statusInfo) return '#9ca3af';
    return getStatusColor(attr.statusInfo);
  };

  // Node styles with width/height
  const nodeStyle = {
    width: `${data.width || 200}px`,
    height: `${data.height || 150}px`,
    minWidth: '150px',
    minHeight: '100px',
  };

  // Get attributes from either old parameters format or new attributes format
  const attributes = data.attributes || [];
  const parameters = data.parameters || {};
  const visibleOnMap = data.visible_on_map || [];
  const statusData = data.statusData || {};
  const parametersStatus = statusData.parameters || {};

  // For backward compatibility, also show old-style parameters
  const oldStyleParams = Object.entries(parameters)
    .filter(([name]) => visibleOnMap.includes(name))
    .map(([name, param]) => ({
      name,
      type: param.type === 'ok/nok' ? 'ok_nok' : 'text',
      label: name,
      statusInfo: parametersStatus[name] || null,
    }));

  // Map new attributes with their status info
  const newAttributes = attributes.map(attr => ({
    ...attr,
    statusInfo: parametersStatus[attr.name] || null,
  }));

  const allAttributes = [...newAttributes, ...oldStyleParams];

  return (
    <div
      className={`container-node ${selected ? 'selected' : ''} ${data.locked ? 'locked' : ''}`}
      style={{ ...nodeStyle, zIndex: data.zIndex || 100 }}
    >
      <Handle type="target" position={Position.Top} />

      {/* Header with status */}
      <div className="node-header">
        <h4>{data.name}</h4>
        <div
          className="status-indicator"
          style={{ backgroundColor: getStatusColor(data.statusData) }}
          title={`Status: ${data.statusData?.status || data.status || 'unknown'}`}
        />
      </div>

      {/* Attributes list */}
      <div className="node-attributes">
        {allAttributes.map((attr, idx) => {
          if (attr.type === 'ok_nok') {
            // OK/NOK attribute - show a colored dot
            const color = getAttributeStatusColor(attr);
            return (
              <div key={attr.name || idx} className="attribute-row ok-nok-row">
                <span className="attribute-label">{attr.label || attr.name}</span>
                <div
                  className="ok-nok-dot"
                  style={{
                    backgroundColor: color,
                    boxShadow: `0 0 4px ${color}`,
                  }}
                  title={`Status: ${attr.statusInfo?.status || 'unknown'}${
                    attr.statusInfo?.value ? ` (${attr.statusInfo.value})` : ''
                  }`}
                />
              </div>
            );
          } else if (attr.type === 'text') {
            // Text attribute - show truncated preview
            const textValue = attr.statusInfo?.value || attr.statusInfo?.text || '...';
            const displayValue =
              textValue.length > 25 ? textValue.substring(0, 25) + '...' : textValue;

            return (
              <div key={attr.name || idx} className="attribute-row text-row">
                <span className="attribute-label">{attr.label || attr.name}:</span>
                <span className="attribute-value" title={textValue}>
                  {displayValue}
                </span>
                {textValue.length > 25 && (
                  <button
                    className="expand-btn"
                    onClick={() => setShowFullText(attr)}
                    title="View full content"
                  >
                    <Maximize2 size={12} />
                  </button>
                )}
              </div>
            );
          }
          // Legacy parameter display
          return (
            <div key={attr.name || idx} className="attribute-row">
              <span className="attribute-label">{attr.label || attr.name}:</span>
              <span className="attribute-value">
                {attr.statusInfo?.value || '...'}
              </span>
            </div>
          );
        })}
      </div>

      {/* Resize handle */}
      {!data.locked && (
        <div
          data-resize-handle="true"
          className="resize-handle"
          title="Drag to resize"
        >
          <svg width="12" height="12" viewBox="0 0 12 12">
            <path d="M9 3v6H6V3h3zm0-1H6a1 1 0 00-1 1v6a1 1 0 001 1h3a1 1 0 001-1V3a1 1 0 00-1-1z" fill="currentColor" />
          </svg>
        </div>
      )}

      {/* Edit button */}
      {!data.locked && (
        <button
          className="edit-btn"
          title="Edit container"
          onClick={() => data.onEdit && data.onEdit(data.id)}
        >
          <Settings size={14} />
        </button>
      )}

      <Handle type="source" position={Position.Bottom} />

      {/* Text modal rendered via portal outside ReactFlow */}
      <TextModal attr={showFullText} onClose={() => setShowFullText(null)} />
    </div>
  );
};

export default ContainerNode;
