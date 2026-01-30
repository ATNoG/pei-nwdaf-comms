/**
 * Custom React Flow node component for image layers.
 * Displays an image with name label, supports inline editing and resizing.
 */
import React, { useState, useCallback } from 'react';

const ImageNode = ({ data, selected }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(data.name);

  // Handle double-click to edit name
  const handleDoubleClick = useCallback(() => {
    if (!data.locked) {
      setIsEditing(true);
    }
  }, [data.locked]);

  // Handle name input blur/enter
  const handleNameSubmit = useCallback(() => {
    setIsEditing(false);
    if (data.onEdit && name !== data.name) {
      data.onEdit(data.id, { ...data, name });
    }
  }, [data, name]);

  // Z-index based on layer type
  const zIndex = data.layer_type === 'background' ? 0 : 1000;

  // In click-through mode, image has no pointer events (except name label and resize handle)
  // This allows clicks to pass through to boxes below
  const clickThroughMode = data.clickThroughMode || false;

  return (
    <div
      style={{
        width: data.width,
        height: data.height,
        position: 'relative',
        borderRadius: '4px',
        overflow: 'hidden',
        zIndex,
        border: selected ? '2px solid #3b82f6' : '2px solid transparent',
        pointerEvents: clickThroughMode ? 'none' : 'auto',
      }}
      onDoubleClick={handleDoubleClick}
    >
      {/* Image */}
      <img
        src={data.url}
        alt={data.name}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          pointerEvents: 'none',
          display: 'block',
        }}
        draggable={false}
        onClick={(e) => {
          // In click-through mode, prevent image clicks from propagating
          if (clickThroughMode) {
            e.stopPropagation();
          }
        }}
      />

      {/* Name label */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: '4px 8px',
          fontSize: '12px',
          fontWeight: '500',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          pointerEvents: 'auto',
        }}
      >
        {isEditing ? (
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={handleNameSubmit}
            onKeyDown={(e) => e.key === 'Enter' && handleNameSubmit()}
            onClick={(e) => e.stopPropagation()}
            onMouseDown={(e) => e.stopPropagation()}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'white',
              fontSize: 'inherit',
              fontWeight: 'inherit',
              padding: 0,
              width: '100%',
              outline: 'none',
            }}
            autoFocus
          />
        ) : (
          <span>{data.name}</span>
        )}
      </div>

      {/* Resize handle - only show when selected and not locked */}
      {selected && !data.locked && (
        <div
          data-resize-handle="true"
          style={{
            position: 'absolute',
            bottom: 0,
            right: 0,
            width: '20px',
            height: '20px',
            cursor: 'nwse-resize',
            backgroundColor: 'rgba(59, 130, 246, 0.6)',
            borderTopLeftRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            pointerEvents: 'auto',
          }}
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="white">
            <path d="M9 3v6H6V3h3zm0-1H6a1 1 0 00-1 1v6a1 1 0 001 1h3a1 1 0 001-1V3a1 1 0 00-1-1z" />
          </svg>
        </div>
      )}
    </div>
  );
};

export default ImageNode;
