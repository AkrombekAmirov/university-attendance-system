// lib/validations/assignment.ts
import { z } from "zod";

export const assignmentSchema = z.object({
    user_id: z.string().uuid(),
    position_id: z.string().uuid(),
    status: z.enum(["ACTIVE", "BLOCKED", "RESIGNED"]).default("ACTIVE"),
    valid_from: z.string().optional(),
    valid_to: z.string().optional(),
});
