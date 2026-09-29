document.addEventListener('DOMContentLoaded', function() {
    initializeAdmin();
});

function initializeAdmin() {
    if (window.location.pathname === '/admin') {
        initializeTableFeatures();
        initializeSearch();
        initializeFilters();
        updateLastUpdated();
    }
}

function initializeTableFeatures() {
    const table = document.getElementById('ticketsTable');
    if (!table) return;
    window.originalTableData = Array.from(table.querySelectorAll('tbody tr'));
    updateShowingCount();
}

let sortDirection = {};
function sortTable(columnIndex) {
    const table = document.getElementById('ticketsTable');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const currentDir = sortDirection[columnIndex] || 'asc';
    const newDir = currentDir === 'asc' ? 'desc' : 'asc';
    sortDirection[columnIndex] = newDir;
    
    updateSortIcons(columnIndex, newDir);
    
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();
        
        if (columnIndex === 3) {
            const aNum = parseInt(aText) || 0;
            const bNum = parseInt(bText) || 0;
            return newDir === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        if (columnIndex === 7) {
            const aDate = new Date(aText);
            const bDate = new Date(bText);
            return newDir === 'asc' ? aDate - bDate : bDate - aDate;
        }
        
        const comparison = aText.localeCompare(bText);
        return newDir === 'asc' ? comparison : -comparison;
    });
    
    rows.forEach(row => tbody.appendChild(row));
    updateShowingCount();
}

function updateSortIcons(activeColumn, direction) {
    const headers = document.querySelectorAll('#ticketsTable thead th');
    headers.forEach((header, index) => {
        const icon = header.querySelector('i.fa-sort, i.fa-sort-up, i.fa-sort-down');
        if (icon) {
            if (index === activeColumn) {
                icon.className = direction === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
            } else {
                icon.className = 'fas fa-sort';
            }
        }
    });
}

function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    searchInput.addEventListener('input', function() {
        filterTable();
    });
}

function initializeFilters() {
    const countryFilter = document.getElementById('countryFilter');
    if (!countryFilter) return;
    countryFilter.addEventListener('change', function() {
        filterTable();
    });
}

function filterTable() {
    if (!window.originalTableData) return;
    
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
    const countryFilter = document.getElementById('countryFilter')?.value || '';
    const tbody = document.querySelector('#ticketsTable tbody');
    
    tbody.innerHTML = '';
    
    let visibleCount = 0;
    
    window.originalTableData.forEach(row => {
        const rowText = row.textContent.toLowerCase();
        const countryCell = row.cells[5].textContent.trim();
        
        const matchesSearch = searchTerm === '' || rowText.includes(searchTerm);
        const matchesCountry = countryFilter === '' || countryCell === countryFilter;
        
        if (matchesSearch && matchesCountry) {
            tbody.appendChild(row.cloneNode(true));
            visibleCount++;
        }
    });
    
    document.getElementById('showingCount').textContent = visibleCount;
    
    if (visibleCount === 0) {
        showEmptySearchResults();
    }
}

function showEmptySearchResults() {
    const tbody = document.querySelector('#ticketsTable tbody');
    const emptyRow = document.createElement('tr');
    emptyRow.innerHTML = `
        <td colspan="9" class="text-center py-4">
            <i class="fas fa-search fa-2x text-muted mb-2"></i>
            <p class="text-muted mb-0">No tickets match your search criteria</p>
        </td>
    `;
    tbody.appendChild(emptyRow);
}

function updateShowingCount() {
    const tbody = document.querySelector('#ticketsTable tbody');
    if (!tbody) return;
    
    const visibleRows = tbody.querySelectorAll('tr').length;
    const showingElement = document.getElementById('showingCount');
    if (showingElement) {
        showingElement.textContent = visibleRows;
    }
}

function refreshData() {
    const refreshBtn = document.querySelector('button[onclick="refreshData()"]');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Refreshing...';
        refreshBtn.disabled = true;
    }
    
    setTimeout(() => {
        location.reload();
    }, 500);
}

function exportVisible() {
    const table = document.getElementById('ticketsTable');
    if (!table) return;
    
    const visibleRows = Array.from(table.querySelectorAll('tbody tr'));
    if (visibleRows.length === 0) {
        alert('No data to export');
        return;
    }
    
    let csvContent = 'Email,Phone,Name,Tickets,Ticket Number,Country,Region,Timestamp\n';
    
    visibleRows.forEach(row => {
        const cells = Array.from(row.cells).slice(0, 8);
        const rowData = cells.map(cell => {
            let text = cell.textContent.trim();
            if (text.includes(',') || text.includes('"')) {
                text = '"' + text.replace(/"/g, '""') + '"';
            }
            return text;
        });
        csvContent += rowData.join(',') + '\n';
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `ticket_data_filtered_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function updateLastUpdated() {
    const element = document.getElementById('lastUpdated');
    if (element) {
        const now = new Date();
        element.textContent = now.toISOString().slice(0, 19).replace('T', ' ');
    }
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

document.addEventListener('submit', function(e) {
    const form = e.target;
    if (form.tagName === 'FORM') {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            const originalHtml = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Processing...';
            
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
            }, 3000);
        }
    }
});

document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey && e.key === 'r') || e.key === 'F5') {
        if (window.location.pathname === '/admin') {
            e.preventDefault();
            refreshData();
        }
    }
    
    if (e.ctrlKey && e.key === 'f') {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            e.preventDefault();
            searchInput.focus();
            searchInput.select();
        }
    }
    
    if (e.key === 'Escape') {
        const searchInput = document.getElementById('searchInput');
        if (searchInput && searchInput.value) {
            searchInput.value = '';
            filterTable();
        }
    }
});
