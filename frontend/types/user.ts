export interface User {
    id: string;
    username: string;
    full_name?: string | null;
    passport?: string | null;
    email?: string | null;
    turniked_id?: string | null;
    position_title?: string | null;
    org_unit_name?: string | null;
}
