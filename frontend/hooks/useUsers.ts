"use client";

import {useQuery, useMutation, useQueryClient} from "@tanstack/react-query";
import {api} from "@/lib/api";
import {toast} from "sonner";
import {User} from "@/types/user";

interface UsersResponse {
    data: User[];
    total: number;
    page: number;
    limit: number;
}

// Users hook
export function useUsers(search: string = "", page: number = 1, limit: number = 50) {
    return useQuery({
        queryKey: ["users", search, page, limit],
        queryFn: async (): Promise<UsersResponse> => {
            const params = new URLSearchParams({
                page: page.toString(),
                limit: limit.toString(),
            });
            
            if (search.trim()) {
                params.append("search", search.trim());
            }

            const response = await api.get<UsersResponse>(`/users/list_full?${params}`);
            return response.data;
        },
        staleTime: 2 * 60 * 1000, // 2 daqiqa
        placeholderData: (previousData) => previousData,
    });
}

// Reload users function
export function useReloadUsers() {
    const queryClient = useQueryClient();
    
    return () => {
        queryClient.invalidateQueries({queryKey: ["users"]});
    };
}

// User actions hook
export function useUserActions() {
    const queryClient = useQueryClient();

    const createUserMutation = useMutation({
        mutationFn: async (userData: FormData) => {
            const response = await api.post("/users/create_simple", userData);
            return response.data;
        },
        onSuccess: () => {
            toast.success("Foydalanuvchi muvaffaqiyatli yaratildi!");
            queryClient.invalidateQueries({queryKey: ["users"]});
        },
        onError: (error: any) => {
            const message = error?.response?.data?.detail || error?.message || "Xatolik yuz berdi";
            toast.error(message);
        },
    });

    const updateUserMutation = useMutation({
        mutationFn: async ({userId, userData}: {userId: string; userData: FormData}) => {
            const response = await api.put(`/users/update_basic/${userId}`, userData);
            return response.data;
        },
        onSuccess: () => {
            toast.success("Muvaffaqiyatli yangilandi!");
            queryClient.invalidateQueries({queryKey: ["users"]});
        },
        onError: (error: any) => {
            const message = error?.response?.data?.detail || error?.message || "Xatolik yuz berdi";
            toast.error(message);
        },
    });

    const assignUserMutation = useMutation({
        mutationFn: async (assignmentData: FormData) => {
            const response = await api.post("/organization/assignments/create", assignmentData);
            return response.data;
        },
        onSuccess: () => {
            toast.success("Foydalanuvchi lavozimga biriktirildi!");
            queryClient.invalidateQueries({queryKey: ["users"]});
        },
        onError: (error: any) => {
            const message = error?.response?.data?.detail || error?.message || "Xatolik yuz berdi";
            toast.error(message);
        },
    });

    const unassignUserMutation = useMutation({
        mutationFn: async (userId: string) => {
            const response = await api.post("/organization/assignments/unassign_all", {
                user_id: userId,
            });
            return response.data;
        },
        onSuccess: () => {
            toast.success("Foydalanuvchi lavozimdan to'liq ozod etildi!");
            queryClient.invalidateQueries({queryKey: ["users"]});
        },
        onError: (error: any) => {
            const message = error?.response?.data?.detail || error?.message || "Xatolik yuz berdi";
            toast.error(message);
        },
    });

    return {
        createUser: createUserMutation.mutateAsync,
        updateUser: updateUserMutation.mutateAsync,
        assignUser: assignUserMutation.mutateAsync,
        unassignUser: unassignUserMutation.mutateAsync,
        isCreating: createUserMutation.isPending,
        isUpdating: updateUserMutation.isPending,
        isAssigning: assignUserMutation.isPending,
        isUnassigning: unassignUserMutation.isPending,
    };
}
