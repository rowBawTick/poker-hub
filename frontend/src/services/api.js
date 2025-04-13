import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

export default {
  /**
   * Get a list of all players
   * @returns {Promise} Promise containing player data
   */
  getPlayers() {
    return apiClient.get('/players');
  },
  
  /**
   * Get statistics for a specific player
   * @param {string} playerName - Name of the player
   * @returns {Promise} Promise containing player statistics
   */
  getPlayerStats(playerName) {
    return apiClient.get(`/player/${encodeURIComponent(playerName)}/stats`);
  },
  
  /**
   * Get recent hands
   * @param {number} limit - Number of hands to retrieve
   * @returns {Promise} Promise containing recent hands data
   */
  getRecentHands(limit = 10) {
    return apiClient.get('/hands/recent', { params: { limit } });
  }
};
