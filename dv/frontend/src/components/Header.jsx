/**
 * Header component with toolbar buttons.
 */
import React from 'react';
import { Lock, Unlock, Plus, Upload, Settings, Trash2, Square, Layers } from 'lucide-react';

const Header = ({
  locked,
  onToggleLock,
  onAddBox,
  onAddImage,
  onAddFrame,
  selectedItem,
  onEditSelected,
  onDeleteSelected,
  clickThroughMode,
  onToggleClickThrough,
}) => {
  return (
    <header className="bg-blue-600 text-white p-4 shadow-md">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Docker Visual Monitor</h1>
        <div className="flex items-center space-x-4">
          <button
            onClick={onToggleLock}
            className={`p-2 rounded-md ${
              locked ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
            } transition-colors`}
            title={locked ? 'Unlock' : 'Lock'}
          >
            {locked ? <Lock size={20} /> : <Unlock size={20} />}
          </button>
          <button
            onClick={onAddBox}
            className="p-2 bg-green-500 rounded-md hover:bg-green-600 transition-colors"
            title="Add Box"
          >
            <Plus size={20} />
          </button>
          <button
            onClick={onAddImage}
            className="p-2 bg-purple-500 rounded-md hover:bg-purple-600 transition-colors"
            title="Add Image"
          >
            <Upload size={20} />
          </button>
          <button
            onClick={onAddFrame}
            className="p-2 bg-orange-500 rounded-md hover:bg-orange-600 transition-colors"
            title="Add Frame"
          >
            <Square size={20} />
          </button>
          <button
            onClick={onToggleClickThrough}
            className={`p-2 rounded-md transition-colors ${
              clickThroughMode
                ? 'bg-teal-500 hover:bg-teal-600'
                : 'bg-gray-500 hover:bg-gray-600'
            }`}
            title={clickThroughMode ? 'Box Mode: Click selects boxes' : 'Image Mode: Click selects images'}
          >
            <Layers size={20} />
          </button>
          {selectedItem && (
            <>
              {selectedItem.type === 'box' && (
                <button
                  onClick={onEditSelected}
                  className="p-2 bg-blue-500 rounded-md hover:bg-blue-600 transition-colors"
                  title="Edit Selected"
                >
                  <Settings size={20} />
                </button>
              )}
              <button
                onClick={onDeleteSelected}
                className="p-2 bg-red-500 rounded-md hover:bg-red-600 transition-colors"
                title={`Delete Selected ${selectedItem.type}`}
              >
                <Trash2 size={20} />
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
