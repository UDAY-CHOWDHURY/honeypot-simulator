import axios from 'axios';

const API_BASE = "http://localhost:5000";  // change if backend is remote

export const triggerSimulation = () =>
  axios.post(`${API_BASE}/simulate`);

export const triggerTrap = () =>
  axios.post(`${API_BASE}/trap`);

export const fetchSimulationLogs = () =>
  axios.get(`${API_BASE}/simulation_logs`);

export const fetchAttackLogs = () =>
  axios.get(`${API_BASE}/attack_logs`);
