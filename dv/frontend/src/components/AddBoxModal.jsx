/**
 * Modal component for adding a new container box.
 */
import React, { useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import apiService from '../services/api';
import { useToast } from '../hooks/useToast';

const AddBoxModal = ({ show, onClose, onBoxAdded }) => {
  const { success, error } = useToast();
  const [newBox, setNewBox] = useState({
    name: '',
    x: 100,
    y: 100,
    status_url: '',
    width: '',
    height: '',
  });

  if (!show) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!newBox.name) {
      error('Name is required');
      return;
    }

    try {
      const id = uuidv4();
      const { width, height, ...boxData } = newBox;
      const boxToAdd = {
        ...boxData,
        id,
        parameters: {},
        attributes: [],
        expanded: false,
        visible_on_map: [],
        width: width ? parseInt(width) : 200,
        height: height ? parseInt(height) : 150,
      };

      await apiService.createBox(boxToAdd);
      success('Box created successfully');
      onBoxAdded(boxToAdd);

      // Reset form
      setNewBox({
        name: '',
        x: 100,
        y: 100,
        status_url: '',
        width: '',
        height: '',
      });
      onClose();
    } catch (err) {
      error(`Failed to create box: ${err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-96 max-h-screen overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">Add New Box</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={newBox.name}
              onChange={(e) => setNewBox({ ...newBox, name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status URL</label>
            <input
              type="url"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={newBox.status_url}
              onChange={(e) => setNewBox({ ...newBox, status_url: e.target.value })}
              placeholder="https://example.com/status"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">X Position</label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newBox.x}
                onChange={(e) => setNewBox({ ...newBox, x: parseInt(e.target.value) || 0 })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Y Position</label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newBox.y}
                onChange={(e) => setNewBox({ ...newBox, y: parseInt(e.target.value) || 0 })}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Width</label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newBox.width}
                onChange={(e) => setNewBox({ ...newBox, width: e.target.value })}
                placeholder="Auto"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Height</label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newBox.height}
                onChange={(e) => setNewBox({ ...newBox, height: e.target.value })}
                placeholder="Auto"
              />
            </div>
          </div>
          <div className="flex justify-end mt-6 space-x-2">
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
              Add Box
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddBoxModal;
