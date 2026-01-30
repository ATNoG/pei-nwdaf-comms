/**
 * Modal component for editing an existing container box.
 */
import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, Trash2, Plus } from 'lucide-react';
import apiService from '../services/api';
import { useToast } from '../hooks/useToast';
import { pendingUpdatesRef } from '../hooks/useDashboardState';

const EditBoxModal = ({ show, box, onClose, onBoxUpdated }) => {
  const { success, error: showError } = useToast();
  const [editingBox, setEditingBox] = useState(null);
  const [newAttr, setNewAttr] = useState({ name: '', label: '', type: 'ok_nok', url: '' });

  useEffect(() => {
    if (box) {
      setEditingBox({ ...box });
    }
  }, [box]);

  if (!show || !editingBox) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Mark this box as having a pending update ONLY during the save operation
    pendingUpdatesRef.current.add(editingBox.id);

    try {
      // Only send the fields that are needed - don't include position object
      const updateData = {
        id: editingBox.id,
        name: editingBox.name,
        x: editingBox.x || 0,
        y: editingBox.y || 0,
        status_url: editingBox.status_url,
        parameters: editingBox.parameters || {},
        attributes: editingBox.attributes || [],
        expanded: editingBox.expanded || false,
        visible_on_map: editingBox.visible_on_map || [],
        width: editingBox.width,
        height: editingBox.height,
      };
      await apiService.updateBox(editingBox.id, updateData);
      success('Box updated successfully');

      // Call onBoxUpdated to trigger optimistic update in parent
      if (onBoxUpdated) {
        onBoxUpdated(editingBox);
      }

      onClose();

      // Remove pending flag after a short delay to allow WebSocket to propagate
      setTimeout(() => {
        pendingUpdatesRef.current.delete(editingBox.id);
      }, 1500);
    } catch (err) {
      showError(`Failed to update box: ${err.message}`);
      // Remove pending flag on error
      pendingUpdatesRef.current.delete(editingBox.id);
    }
  };

  const addAttribute = () => {
    if (!newAttr.name || !newAttr.label) {
      showError('Attribute name and label are required');
      return;
    }

    if (newAttr.type !== 'ok_nok' && newAttr.type !== 'text') {
      showError('Type must be ok_nok or text');
      return;
    }

    setEditingBox((prev) => ({
      ...prev,
      attributes: [
        ...(prev.attributes || []),
        {
          name: newAttr.name,
          label: newAttr.label,
          type: newAttr.type,
          url: newAttr.url || undefined,
        },
      ],
    }));

    setNewAttr({ name: '', label: '', type: 'ok_nok', url: '' });
  };

  const removeAttribute = (index) => {
    setEditingBox((prev) => ({
      ...prev,
      attributes: prev.attributes.filter((_, i) => i !== index),
    }));
  };

  // Legacy parameters support
  const addParameter = () => {
    if (!newAttr.name) {
      showError('Parameter name is required');
      return;
    }

    setEditingBox((prev) => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [newAttr.name]: {
          type: newAttr.type === 'ok_nok' ? 'ok/nok' : 'text',
          length: 50,
        },
      },
    }));

    setNewAttr({ name: '', label: '', type: 'ok_nok', url: '' });
  };

  const removeParameter = (paramName) => {
    const newParameters = { ...editingBox.parameters };
    delete newParameters[paramName];

    setEditingBox((prev) => ({
      ...prev,
      parameters: newParameters,
      visible_on_map: (prev.visible_on_map || []).filter((p) => p !== paramName),
    }));
  };

  const toggleParameterVisibility = (paramName) => {
    const isVisible = editingBox.visible_on_map && editingBox.visible_on_map.includes(paramName);

    setEditingBox((prev) => ({
      ...prev,
      visible_on_map: isVisible
        ? prev.visible_on_map.filter((p) => p !== paramName)
        : [...(prev.visible_on_map || []), paramName],
    }));
  };

  const hasAttributes = editingBox.attributes && editingBox.attributes.length > 0;
  const hasLegacyParams = editingBox.parameters && Object.keys(editingBox.parameters).length > 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-[500px] max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">Edit Box: {editingBox.name}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Basic Info */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={editingBox.name}
              onChange={(e) => setEditingBox({ ...editingBox, name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status URL</label>
            <input
              type="url"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={editingBox.status_url || ''}
              onChange={(e) => setEditingBox({ ...editingBox, status_url: e.target.value })}
              placeholder="https://api.example.com/status"
            />
          </div>

          {/* Dimensions */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Width (px)</label>
              <input
                type="number"
                min="150"
                max="2000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={editingBox.width || 200}
                onChange={(e) =>
                  setEditingBox({
                    ...editingBox,
                    width: e.target.value ? Math.min(2000, Math.max(150, parseInt(e.target.value))) : 200,
                  })
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Height (px)</label>
              <input
                type="number"
                min="100"
                max="2000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={editingBox.height || 150}
                onChange={(e) =>
                  setEditingBox({
                    ...editingBox,
                    height: e.target.value ? Math.min(2000, Math.max(100, parseInt(e.target.value))) : 150,
                  })
                }
              />
            </div>
          </div>

          {/* New Attributes Section */}
          <div className="border-t pt-4">
            <h3 className="text-md font-semibold mb-2">Attributes</h3>
            <p className="text-xs text-gray-500 mb-2">
              Add attributes to monitor specific endpoints. Each attribute will be polled independently.
            </p>

            {hasAttributes && (
              <div className="space-y-2 mb-4 max-h-48 overflow-y-auto">
                {editingBox.attributes.map((attr, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-100 rounded">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{attr.label}</div>
                      <div className="text-xs text-gray-500">
                        <span className="capitalize">{attr.type}</span>
                        {attr.url && (
                          <span className="ml-2 truncate inline-block max-w-[200px]" title={attr.url}>
                            {attr.url}
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="p-1 text-red-500 hover:bg-red-100 rounded flex-shrink-0"
                      onClick={() => removeAttribute(index)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="border-t pt-2 space-y-2">
              <input
                type="text"
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                placeholder="Attribute ID (e.g., cpu_usage)"
                value={newAttr.name}
                onChange={(e) => setNewAttr({ ...newAttr, name: e.target.value })}
              />
              <input
                type="text"
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                placeholder="Display Label (e.g., CPU Usage)"
                value={newAttr.label}
                onChange={(e) => setNewAttr({ ...newAttr, label: e.target.value })}
              />
              <select
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                value={newAttr.type}
                onChange={(e) => setNewAttr({ ...newAttr, type: e.target.value })}
              >
                <option value="ok_nok">OK/NOK (colored dot)</option>
                <option value="text">Text (display content)</option>
              </select>
              <input
                type="url"
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                placeholder="URL to check (optional, uses status URL if empty)"
                value={newAttr.url}
                onChange={(e) => setNewAttr({ ...newAttr, url: e.target.value })}
              />
              <button
                type="button"
                className="w-full px-2 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors flex items-center justify-center gap-1"
                onClick={addAttribute}
              >
                <Plus size={14} />
                Add Attribute
              </button>
            </div>
          </div>

          {/* Legacy Parameters Section */}
          {hasLegacyParams && (
            <div className="border-t pt-4">
              <h3 className="text-md font-semibold mb-2">Legacy Parameters</h3>
              <p className="text-xs text-yellow-600 mb-2">
                These are the old-style parameters. Consider migrating to attributes above.
              </p>
              <div className="space-y-2 mb-4">
                {Object.entries(editingBox.parameters).map(([name, param]) => (
                  <div key={name} className="flex items-center justify-between p-2 bg-yellow-50 rounded">
                    <div>
                      <span className="font-medium">{name}</span>
                      <span className="text-sm text-gray-500 ml-2">({param.type})</span>
                      {editingBox.visible_on_map && editingBox.visible_on_map.includes(name) && (
                        <span className="ml-2 text-sm text-blue-500 flex items-center gap-1">
                          <Eye size={14} className="inline" />
                          Visible
                        </span>
                      )}
                    </div>
                    <div className="flex space-x-1">
                      <button
                        type="button"
                        className="p-1 text-blue-500 hover:bg-blue-100 rounded"
                        onClick={() => toggleParameterVisibility(name)}
                      >
                        {editingBox.visible_on_map && editingBox.visible_on_map.includes(name) ? (
                          <EyeOff size={16} />
                        ) : (
                          <Eye size={16} />
                        )}
                      </button>
                      <button
                        type="button"
                        className="p-1 text-red-500 hover:bg-red-100 rounded"
                        onClick={() => removeParameter(name)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end mt-6 space-x-2 pt-4 border-t">
            <button
              type="button"
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditBoxModal;
