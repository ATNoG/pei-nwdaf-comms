/**
 * Modal component for adding a new frame.
 */
import React, { useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import apiService from '../services/api';
import { useToast } from '../hooks/useToast';

const AddFrameModal = ({ show, onClose, onFrameAdded }) => {
  const { success, error } = useToast();
  const [newFrame, setNewFrame] = useState({
    name: '',
    x: 100,
    y: 100,
    width: 400,
    height: 300,
    border_color: '#3b82f6',
    border_width: 2,
    border_style: 'solid',
  });

  if (!show) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!newFrame.name) {
      error('Name is required');
      return;
    }

    try {
      const id = 'frame_' + uuidv4().replace(/-/g, '').substring(0, 8);
      const frameToAdd = { ...newFrame, id };

      await apiService.createFrame(frameToAdd);
      success('Frame added successfully');
      onFrameAdded(frameToAdd);

      // Reset form
      setNewFrame({
        name: '',
        x: 100,
        y: 100,
        width: 400,
        height: 300,
        border_color: '#3b82f6',
        border_width: 2,
        border_style: 'solid',
      });
      onClose();
    } catch (err) {
      error(`Failed to add frame: ${err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-96 max-h-screen overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">Add New Frame</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={newFrame.name}
              onChange={(e) => setNewFrame({ ...newFrame, name: e.target.value })}
              placeholder="My Frame"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">X Position</label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newFrame.x}
                onChange={(e) => setNewFrame({ ...newFrame, x: parseInt(e.target.value) || 0 })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Y Position</label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newFrame.y}
                onChange={(e) => setNewFrame({ ...newFrame, y: parseInt(e.target.value) || 0 })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Width</label>
              <input
                type="number"
                min="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newFrame.width}
                onChange={(e) => setNewFrame({ ...newFrame, width: parseInt(e.target.value) || 400 })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Height</label>
              <input
                type="number"
                min="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newFrame.height}
                onChange={(e) => setNewFrame({ ...newFrame, height: parseInt(e.target.value) || 300 })}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Border Color</label>
            <div className="flex items-center space-x-2">
              <input
                type="color"
                className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                value={newFrame.border_color}
                onChange={(e) => setNewFrame({ ...newFrame, border_color: e.target.value })}
              />
              <input
                type="text"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newFrame.border_color}
                onChange={(e) => setNewFrame({ ...newFrame, border_color: e.target.value })}
                placeholder="#3b82f6"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Border Width</label>
              <input
                type="number"
                min="1"
                max="20"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newFrame.border_width}
                onChange={(e) => setNewFrame({ ...newFrame, border_width: parseInt(e.target.value) || 2 })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Border Style</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newFrame.border_style}
                onChange={(e) => setNewFrame({ ...newFrame, border_style: e.target.value })}
              >
                <option value="solid">Solid</option>
                <option value="dashed">Dashed</option>
                <option value="dotted">Dotted</option>
                <option value="double">Double</option>
              </select>
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
              Add Frame
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddFrameModal;
