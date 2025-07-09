// utils/statusUtils.js
export const getStatusColor = (status) => {
    switch (status) {
        case 'Active': 
            return 'status-active';
        case 'Rest': 
            return 'status-rest';
        case 'Completed': 
            return 'status-completed';
        case 'In Progress': 
            return 'status-in-progress';
        case 'Pending': 
            return 'status-pending';
        case 'Pre-OP':
            return 'status-pre-op';
        case 'Post-OP':
            return 'status-post-op';
        default: 
            return 'status-pending';
    }
};