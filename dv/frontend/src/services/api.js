/**
 * API service for backend communication.
 * Handles all HTTP requests to the backend API.
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  /**
   * Create an axios instance with default configuration.
   */
  getAxiosConfig() {
    return {
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    };
  }

  /**
   * Handle API errors consistently.
   */
  handleError(error, context = 'API request') {
    console.error(`${context} failed:`, error);

    if (error.response) {
      // Server responded with error status
      return {
        message: error.response.data?.detail || error.response.statusText || 'Request failed',
        status: error.response.status,
      };
    } else if (error.request) {
      // Request made but no response
      return {
        message: 'No response from server. Check your connection.',
        status: null,
      };
    } else {
      // Error setting up request
      return {
        message: error.message || 'Unknown error occurred',
        status: null,
      };
    }
  }

  // State endpoints
  async getState() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/state`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Get state');
    }
  }

  async updateState(state) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/state`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Update state');
    }
  }

  // Box endpoints
  async getBoxes() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/boxes`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Get boxes');
    }
  }

  async createBox(box) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/boxes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(box),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Create box');
    }
  }

  async updateBox(boxId, box) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/boxes/${boxId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(box),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Update box');
    }
  }

  async deleteBox(boxId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/boxes/${boxId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Delete box');
    }
  }

  // Line endpoints
  async getLines() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lines`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Get lines');
    }
  }

  async createLine(line) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lines`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(line),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Create line');
    }
  }

  async updateLine(lineId, line) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lines/${lineId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(line),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Update line');
    }
  }

  async deleteLine(lineId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/lines/${lineId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Delete line');
    }
  }

  // Image endpoints
  async getImages() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/images`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Get images');
    }
  }

  async createImage(image) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/images`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(image),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Create image');
    }
  }

  async updateImage(imageId, image) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/images/${imageId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(image),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Update image');
    }
  }

  async deleteImage(imageId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/images/${imageId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Delete image');
    }
  }

  // Frame endpoints
  async getFrames() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/frames`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Get frames');
    }
  }

  async createFrame(frame) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/frames`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(frame),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Create frame');
    }
  }

  async updateFrame(frameId, frame) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/frames/${frameId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(frame),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Update frame');
    }
  }

  async deleteFrame(frameId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/frames/${frameId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Delete frame');
    }
  }

  // File upload
  async uploadFile(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/api/images/upload`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Upload file');
    }
  }

  // Status endpoints
  async getBoxStatus(boxId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/status/${boxId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Get box status');
    }
  }

  async getLineStatus(lineId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/line-status/${lineId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Get line status');
    }
  }

  // Toggle lock
  async toggleLock() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/toggle-lock`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Toggle lock');
    }
  }

  // Set view
  async setView(zoom, panX, panY) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/set-view`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zoom, pan_x: panX, pan_y: panY }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Set view');
    }
  }

  // Health check
  async getHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      throw this.handleError(error, 'Health check');
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
