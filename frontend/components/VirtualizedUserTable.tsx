"use client";

import {useCallback, useMemo} from "react";
// @ts-ignore
import {FixedSizeList as List} from "react-window";
// @ts-ignore
import AutoSizer from "react-virtualized-auto-sizer";
import {Button} from "@/components/ui/button";
import {Plus, X, Pencil, Link2} from "lucide-react";
import {User} from "@/types/user";

interface VirtualizedUserTableProps {
    users: User[];
    onEdit: (user: User) => void;
    onAssign: (user: User) => void;
    onUnassign: (user: User) => void;
    isUnassigning?: boolean;
}

const ROW_HEIGHT = 60;
const HEADER_HEIGHT = 40;

const UserRow = ({index, style, data}: {index: number; style: any; data: any}) => {
    const {users, onEdit, onAssign, onUnassign, isUnassigning} = data;
    const user = users[index];

    return (
        <div style={style} className="border-b hover:bg-gray-50 transition-colors">
            <div className="grid grid-cols-7 gap-2 p-3 text-sm items-center">
                <div className="font-medium truncate">{user.full_name || "-"}</div>
                <div className="text-gray-600 truncate">{user.username}</div>
                <div className="truncate">{user.position_title || "-"}</div>
                <div className="truncate">{user.org_unit_name || "-"}</div>
                <div className="truncate">{user.turniked_id || "-"}</div>
                <div className="text-gray-600 truncate">{user.email || "-"}</div>
                <div>
                    <div className="flex gap-1 justify-end">
                        {/* Unassign Button */}
                        <Button
                            size="sm"
                            variant="outline"
                            disabled={!user.position_title || isUnassigning}
                            onClick={() => onUnassign(user)}
                            className="border-red-300 text-red-600 hover:bg-red-50 px-2 py-1"
                        >
                            <X size={14}/>
                        </Button>

                        {/* Assign Button */}
                        <Button
                            size="sm"
                            className="bg-purple-600 hover:bg-purple-700 text-white px-2 py-1"
                            onClick={() => onAssign(user)}
                        >
                            <Link2 size={14}/>
                        </Button>

                        {/* Edit Button */}
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onEdit(user)}
                            className="px-2 py-1"
                        >
                            <Pencil size={14}/>
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export function VirtualizedUserTable({
    users,
    onEdit,
    onAssign,
    onUnassign,
    isUnassigning = false,
}: VirtualizedUserTableProps) {
    const rowData = useMemo(
        () => ({
            users,
            onEdit,
            onAssign,
            onUnassign,
            isUnassigning,
        }),
        [users, onEdit, onAssign, onUnassign, isUnassigning]
    );

    if (users.length === 0) {
        return (
            <div className="text-center py-8 text-gray-500">
                Hech narsa topilmadi
            </div>
        );
    }

    return (
        <div className="h-[600px] border rounded-lg overflow-hidden">
            {/* Header */}
            <div
                className="bg-gray-50 text-left border-b font-medium text-gray-700"
                style={{height: HEADER_HEIGHT}}
            >
                <div className="grid grid-cols-7 gap-2 p-3 text-sm items-center">
                    <div>F.I.Sh</div>
                    <div>Username</div>
                    <div>Lavozim</div>
                    <div>Bo'lim</div>
                    <div>Turniket ID</div>
                    <div>Email</div>
                    <div className="text-right">Harakatlar</div>
                </div>
            </div>

            {/* Virtualized List */}
            <div style={{height: `calc(100% - ${HEADER_HEIGHT}px)`}}>
                <AutoSizer>
                    {({height, width}: {height: number, width: number}) => (
                        <List
                            height={height}
                            width={width}
                            itemCount={users.length}
                            itemSize={ROW_HEIGHT}
                            itemData={rowData}
                            overscanCount={5}
                        >
                            {UserRow}
                        </List>
                    )}
                </AutoSizer>
            </div>
        </div>
    );
}
