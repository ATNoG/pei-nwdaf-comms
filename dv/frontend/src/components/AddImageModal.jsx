/**
 * Modal component for adding a new image layer.
 */
import React, { useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import apiService from '../services/api';
import { useToast } from '../hooks/useToast';

const AddImageModal = ({ show, onClose, onImageAdded }) => {
  const { success, error } = useToast();
  const [newImage, setNewImage] = useState({
    name: '',
    layer_type: 'background',
    url: '',
    x: 0,
    y: 0,
    width: 800,
    height: 600,
  });
  const [uploading, setUploading] = useState(false);

  if (!show) return null;

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    try {
      const response = await apiService.uploadFile(file);
      // Construct full URL from relative path
      const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const fullUrl = response.url.startsWith('http')
        ? response.url
        : `${apiBaseUrl}${response.url}`;
      setNewImage((prev) => ({ ...prev, url: fullUrl }));
      success('File uploaded successfully');
    } catch (err) {
      error(`Failed to upload file: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!newImage.name) {
      error('Name is required');
      return;
    }

    if (!newImage.url) {
      error('Image URL is required');
      return;
    }

    try {
      const id = uuidv4();
      const imageToAdd = { ...newImage, id };

      await apiService.createImage(imageToAdd);
      success('Image added successfully');
      onImageAdded(imageToAdd);

      // Reset form
      setNewImage({
        name: '',
        layer_type: 'background',
        url: '',
        x: 0,
        y: 0,
        width: 800,
        height: 600,
      });
      onClose();
    } catch (err) {
      error(`Failed to add image: ${err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-96 max-h-screen overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">Add New Image</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={newImage.name}
              onChange={(e) => setNewImage({ ...newImage, name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Layer Type</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={newImage.layer_type}
              onChange={(e) => setNewImage({ ...newImage, layer_type: e.target.value })}
            >
              <option value="background">Background</option>
              <option value="foreground">Foreground</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Image URL *</label>
            <input
              type="url"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={newImage.url}
              onChange={(e) => setNewImage({ ...newImage, url: e.target.value })}
              placeholder="https://example.com/image.jpg"
            />
            <div className="mt-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Or Upload Image</label>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                disabled={uploading}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              {uploading && <p className="text-sm text-gray-500 mt-1">Uploading...</p>}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">X Position</label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newImage.x}
                onChange={(e) => setNewImage({ ...newImage, x: parseInt(e.target.value) || 0 })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Y Position</label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newImage.y}
                onChange={(e) => setNewImage({ ...newImage, y: parseInt(e.target.value) || 0 })}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Width</label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newImage.width}
                onChange={(e) => setNewImage({ ...newImage, width: parseInt(e.target.value) || 800 })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Height</label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={newImage.height}
                onChange={(e) => setNewImage({ ...newImage, height: parseInt(e.target.value) || 600 })}
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
              Add Image
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddImageModal;
