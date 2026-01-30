/**
 * Custom React Flow node component for frames.
 * A frame is a transparent rectangle with a colored border, used for decoration.
 * It sits below all other elements and allows clicking through to select items inside.
 */
import React, { useState, useCallback } from 'react';

const FrameNode = ({ data, selected }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(data.name);

  // Handle double-click to edit name
  const handleDoubleClick = useCallback((e) => {
    e.stopPropagation();
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

  // Get border style based on border_style property
  const getBorderStyle = (style) => {
    switch (style) {
      case 'dashed':
        return 'dashed';
      case 'dotted':
        return 'dotted';
      case 'double':
        return 'double';
      default:
        return 'solid';
    }
  };

  return (
    <div
      style={{
        width: data.width,
        height: data.height,
        position: 'relative',
        border: `${data.border_width || 2}px ${getBorderStyle(data.border_style)} ${data.border_color || '#3b82f6'}`,
        backgroundColor: 'transparent',
        borderRadius: '4px',
        zIndex: -1, // Always below other elements
        pointerEvents: 'none', // Allow click-through to select elements inside
      }}
      onDoubleClick={handleDoubleClick}
    >
      {/* Name label - top-left corner, pointer events enabled */}
      <div
        style={{
          position: 'absolute',
          top: '-24px',
          left: '0',
          backgroundColor: data.border_color || '#3b82f6',
          color: 'white',
          padding: '2px 8px',
          fontSize: '12px',
          fontWeight: '500',
          borderRadius: '4px 4px 0 0',
          pointerEvents: 'auto',
          whiteSpace: 'nowrap',
        }}
        onDoubleClick={handleDoubleClick}
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
              minWidth: '60px',
            }}
            autoFocus
          />
        ) : (
          <span>{data.name}</span>
        )}
      </div>

      {/* Selection indicator - only visible when selected */}
      {selected && (
        <div
          style={{
            position: 'absolute',
            top: '-2px',
            left: '-2px',
            right: '-2px',
            bottom: '-2px',
            border: '2px solid #3b82f6',
            borderRadius: '6px',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Resize handle - bottom-right corner */}
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

export default FrameNode;
