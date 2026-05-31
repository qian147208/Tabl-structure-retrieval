/**
 * 数据字典导出平台 - 前端交互逻辑
 */

let tables = [];
let selectedTables = [];

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('connect-form')) {
        initLoginPage();
    } else if (document.getElementById('table-list')) {
        initTablesPage();
    }
});

function initLoginPage() {
    const btnTest = document.getElementById('btn-test');
    const btnConnect = document.getElementById('btn-connect');
    
    if (btnTest) {
        btnTest.addEventListener('click', testConnection);
    }
    
    if (btnConnect) {
        btnConnect.addEventListener('click', connectAndExport);
    }
}

async function testConnection() {
    const data = getFormData();
    const error = validateForm(data);
    
    if (error) {
        showError(error);
        return;
    }
    
    hideAlerts();
    setButtonLoading(document.getElementById('btn-test'), true);
    
    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess(`连接成功！找到 ${result.tables.length} 个表`);
            await fetch('/api/disconnect', { method: 'POST' });
        } else {
            showError(result.message);
        }
    } catch (err) {
        showError('连接失败，请检查网络或服务器状态');
        console.error(err);
    } finally {
        setButtonLoading(document.getElementById('btn-test'), false);
    }
}

async function connectAndExport() {
    const data = getFormData();
    const error = validateForm(data);
    
    if (error) {
        showError(error);
        return;
    }
    
    hideAlerts();
    setButtonLoading(document.getElementById('btn-connect'), true);
    
    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = '/tables';
        } else {
            showError(result.message);
        }
    } catch (err) {
        showError('连接失败，请检查网络或服务器状态');
        console.error(err);
    } finally {
        setButtonLoading(document.getElementById('btn-connect'), false);
    }
}

function getFormData() {
    return {
        db_type: document.querySelector('input[name="db_type"]:checked')?.value || 'mysql',
        host: document.getElementById('host')?.value || '',
        port: document.getElementById('port')?.value || '',
        user: document.getElementById('user')?.value || '',
        password: document.getElementById('password')?.value || '',
        database: document.getElementById('database')?.value || ''
    };
}

function validateForm(data) {
    if (!data.host.trim()) return '请输入主机地址';
    if (!data.port.trim()) return '请输入端口';
    if (!data.user.trim()) return '请输入用户名';
    if (!data.database.trim()) return '请输入数据库名称';
    return null;
}

function showError(message) {
    const alertDiv = document.getElementById('alert-error');
    const messageSpan = document.getElementById('error-message');
    
    if (alertDiv && messageSpan) {
        messageSpan.textContent = message;
        alertDiv.style.display = 'block';
        document.getElementById('alert-success').style.display = 'none';
    }
}

function showSuccess(message) {
    const alertDiv = document.getElementById('alert-success');
    const messageSpan = document.getElementById('success-message');
    
    if (alertDiv && messageSpan) {
        messageSpan.textContent = message;
        alertDiv.style.display = 'block';
        document.getElementById('alert-error').style.display = 'none';
    }
}

function hideAlerts() {
    const alertError = document.getElementById('alert-error');
    const alertSuccess = document.getElementById('alert-success');
    
    if (alertError) alertError.style.display = 'none';
    if (alertSuccess) alertSuccess.style.display = 'none';
}

function setButtonLoading(btn, loading) {
    if (!btn) return;
    
    const spinner = btn.querySelector('.spinner');
    
    if (loading) {
        btn.disabled = true;
        if (spinner) spinner.style.display = 'inline-block';
    } else {
        btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
    }
}

async function initTablesPage() {
    await loadDbInfo();
    await loadTables();
    bindEvents();
}

async function loadDbInfo() {
    try {
        const response = await fetch('/api/db_info');
        const result = await response.json();
        
        if (result.success && result.db_info) {
            document.getElementById('db-name').textContent = 
                `${result.db_info.db_type}://${result.db_info.host}/${result.db_info.database}`;
        }
    } catch (err) {
        console.error('加载数据库信息失败:', err);
    }
}

async function loadTables() {
    try {
        const container = document.getElementById('table-list');
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⏳</div>
                <div>加载表中...</div>
            </div>
        `;
        
        const response = await fetch('/api/db_info');
        if (!response.ok) {
            window.location.href = '/';
            return;
        }
        
        const connectResponse = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reconnect: true })
        });
        
        const result = await connectResponse.json();
        
        if (result.success) {
            tables = result.tables;
            selectedTables = [];
            renderTableList(tables);
        } else {
            window.location.href = '/';
        }
    } catch (err) {
        console.error('加载表列表失败:', err);
        window.location.href = '/';
    }
}

function renderTableList(tableList) {
    const container = document.getElementById('table-list');
    
    if (!tableList || tableList.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📦</div>
                <div class="empty-text">没有找到数据表</div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = tableList.map(table => `
        <div class="table-item ${selectedTables.includes(table) ? 'selected' : ''}" 
             data-table="${table}">
            <div class="table-checkbox"></div>
            <div class="table-icon">📊</div>
            <div class="table-name">${table}</div>
        </div>
    `).join('');
    
    document.querySelectorAll('.table-item').forEach(item => {
        item.addEventListener('click', () => {
            const tableName = item.dataset.table;
            toggleTable(tableName);
        });
    });
    
    updateSelectedCount();
}

function toggleTable(tableName) {
    const index = selectedTables.indexOf(tableName);
    
    if (index === -1) {
        selectedTables.push(tableName);
    } else {
        selectedTables.splice(index, 1);
    }
    
    const item = document.querySelector(`.table-item[data-table="${tableName}"]`);
    if (item) {
        item.classList.toggle('selected');
    }
    
    updateSelectedCount();
}

function updateSelectedCount() {
    const countEl = document.getElementById('selected-count');
    if (countEl) {
        countEl.textContent = `✅ 已选择：${selectedTables.length} 个表`;
    }
}

function bindEvents() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const keyword = e.target.value.toLowerCase();
            const filtered = tables.filter(table => table.toLowerCase().includes(keyword));
            renderTableList(filtered);
        });
    }
    
    const btnSelectAll = document.getElementById('btn-select-all');
    if (btnSelectAll) {
        btnSelectAll.addEventListener('click', () => {
            selectedTables = [...tables];
            renderTableList(tables);
        });
    }
    
    const btnDeselectAll = document.getElementById('btn-deselect-all');
    if (btnDeselectAll) {
        btnDeselectAll.addEventListener('click', () => {
            selectedTables = [];
            renderTableList(tables);
        });
    }
    
    document.querySelectorAll('.format-option').forEach(opt => {
        opt.addEventListener('click', () => {
            document.querySelectorAll('.format-option').forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
        });
    });
    
    const btnExport = document.getElementById('btn-export');
    if (btnExport) {
        btnExport.addEventListener('click', exportData);
    }
    
    const btnDisconnect = document.getElementById('btn-disconnect');
    if (btnDisconnect) {
        btnDisconnect.addEventListener('click', disconnect);
    }
}

async function exportData() {
    if (selectedTables.length === 0) {
        alert('请至少选择一个表');
        return;
    }
    
    const formatOption = document.querySelector('.format-option.active');
    let format = 'both';
    
    if (formatOption) {
        const input = formatOption.querySelector('input[type="radio"]');
        if (input) format = input.value;
    }
    
    const btnExport = document.getElementById('btn-export');
    setButtonLoading(btnExport, true);
    
    const progressSection = document.getElementById('progress-section');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    if (progressSection) progressSection.classList.add('show');
    if (progressBar) progressBar.style.width = '30%';
    if (progressText) progressText.textContent = '30%';
    
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tables: selectedTables,
                format: format
            })
        });
        
        const result = await response.json();
        
        if (progressBar) progressBar.style.width = '100%';
        if (progressText) progressText.textContent = '100%';
        
        if (result.success) {
            setTimeout(() => {
                if (progressSection) progressSection.classList.remove('show');
                showExportResult(result);
            }, 500);
        } else {
            alert(result.message);
        }
    } catch (err) {
        alert('导出失败，请检查网络或服务器状态');
        console.error(err);
    } finally {
        setButtonLoading(btnExport, false);
    }
}

function showExportResult(result) {
    const contentEl = document.getElementById('result-content');
    if (!contentEl) return;
    
    let html = '<p style="color: rgba(0, 255, 159, 0.7); margin-bottom: 1rem;">文件已准备好下载:</p>';
    
    result.files.forEach(file => {
        if (file.type === 'file') {
            html += `
                <div class="file-item">
                    <div class="file-info">
                        <span class="file-icon">📊</span>
                        <span class="file-name">${file.name}</span>
                    </div>
                    <a href="${file.path}" class="download-link">
                        下载
                    </a>
                </div>
            `;
        } else {
            html += `
                <div class="file-item">
                    <div class="file-info">
                        <span class="file-icon">📁</span>
                        <span class="file-name">${file.name}</span>
                    </div>
                </div>
            `;
        }
    });
    
    contentEl.innerHTML = html;
    
    const modalElement = document.getElementById('result-modal');
    if (modalElement) {
        modalElement.classList.add('show');
    }
}

async function disconnect() {
    if (confirm('确定要断开数据库连接吗？')) {
        try {
            await fetch('/api/disconnect', { method: 'POST' });
        } catch (e) {
            console.error('断开连接失败:', e);
        }
        window.location.href = '/';
    }
}