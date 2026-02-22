export interface AssignmentCreateIn {
    user_id: string;
    position_id: string;
    valid_from: string;
    valid_to?: string;
    status: 'ACTIVE' | 'INACTIVE';
}
