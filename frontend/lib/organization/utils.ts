import {axios} from '../api';
import { AssignmentCreateIn } from '@/types';

export const getAllPositions = async () => {
    const res = await axios.get('/organization/positions/list');
    return res.data;
};

export const getAllUsers = async () => {
    const res = await axios.get('/users/list'); // Yoki to'g'ri endpointingizni qo'ying
    return res.data;
};

export const createAssignment = async (data: AssignmentCreateIn) => {
    const res = await axios.post('/organization/assignments/create', data);
    return res.data;
};
