// =================================================================
//                 MAIN APPLICATION FILE (app.js)
//         Gộp tất cả các module vào một file duy nhất
// =================================================================

// === MODULE 1: SNIPPET MANAGER ===
const SnippetManager = {
    _buildTreeHtml(nodes) {
        let html = '<ul class="snippet-tree">';
        nodes.forEach(node => {
            if (node.type === 'folder') {
                html += `<li class="snippet-folder"><div class="snippet-folder-header"><i class="fas fa-caret-right folder-toggle"></i><i class="fas fa-folder"></i><span>${node.name}</span></div>${this._buildTreeHtml(node.children || [])}</li>`;
            } else if (node.type === 'snippet') {
                html += `<li class="snippet-item" data-content="${encodeURIComponent(node.content)}"><i class="fas fa-file-alt"></i><span>${node.name}</span></li>`;
            }
        });
        return html + '</ul>';
    },

    async show(editorInstance) {
        try {
            const response = await fetch('/static/snippets.json'); // Đọc từ file JSON
            if (!response.ok) throw new Error('Không thể tải file snippets.json');
            const snippetsData = await response.json();
            const treeHtml = this._buildTreeHtml(snippetsData);
            
            Swal.fire({
                title: '<strong>Kho Snippet</strong>',
                html: `<div id="snippet-tree-container">${treeHtml}</div>`,
                width: '600px', showCloseButton: true, showConfirmButton: false,
                didOpen: () => {
                    document.getElementById('snippet-tree-container').addEventListener('click', (e) => {
                        const folderHeader = e.target.closest('.snippet-folder-header');
                        const snippetItem = e.target.closest('.snippet-item');
                        if (folderHeader) {
                            folderHeader.parentElement.classList.toggle('is-open');
                            folderHeader.querySelector('.folder-toggle').classList.toggle('fa-caret-down');
                        } else if (snippetItem) {
                            const content = decodeURIComponent(snippetItem.dataset.content);
                            editorInstance.getContribution('snippetController2').insert(content);
                            editorInstance.focus();
                            Swal.close();
                        }
                    });
                }
            });
        } catch (error) {
            Swal.fire('Lỗi', `Không thể tải kho snippet: ${error.message}`, 'error');
        }
    }
};

// === MODULE 2: CODE TOOLS ===
const CodeTools = {
    beautifyLatexCode(content) {
        const topLevelEnvs = ['ex', 'vd', 'bt', 'document'];
        const indent = '    ';
        let lines = content.split('\n');
        let beautifiedLines = [];
        let indentLevel = 0;
        lines.forEach(line => {
            let trimmedLine = line.trim();
            if (trimmedLine.length === 0) return;
            const endMatch = trimmedLine.match(/^\\end\{([a-zA-Z*]+)\}/);
            if (endMatch) { if (indentLevel > 0) indentLevel--; }
            beautifiedLines.push(indent.repeat(indentLevel) + trimmedLine);
            const beginMatch = trimmedLine.match(/^\\begin\{([a-zA-Z*]+)\}/);
            if (beginMatch) { indentLevel++; }
        });
        return beautifiedLines.join('\n');
    },
    numberQuestions(text, envs, startNum) {
        let counters = {};
        envs.forEach(env => { counters[env] = startNum; });
        return text.split('\n').map(line => {
            const match = line.match(/\\begin\{(\w+)\}/);
            if (match && envs.includes(match[1])) {
                const num = counters[match[1]]++;
                return `%%========== Câu ${num} (${match[1]}) ==========\n${line}`;
            }
            return line;
        }).join('\n');
    },
    removeLatexComments(text) { return text.split('\n').filter(line => !line.trim().startsWith('%')).join('\n'); },

    async showModal(editorInstance) {
        const { value: formValues } = await Swal.fire({
            title: 'Công cụ xử lý LaTeX',
            html: `... (HTML cho modal công cụ)`, // Copy HTML từ file bạn cung cấp
            confirmButtonText: 'Thực hiện', showCancelButton: true,
            /* ... (didOpen và preConfirm logic) ... */
        });
        if (formValues) {
            let content = editorInstance.getValue();
            if (formValues.doNumbering) content = this.numberQuestions(content, formValues.envs, formValues.startNumber);
            if (formValues.removeComments) content = this.removeLatexComments(content);
            if (formValues.beautify) content = this.beautifyLatexCode(content);
            editorInstance.setValue(content);
            Swal.fire('Hoàn thành!', 'Đã áp dụng.', 'success');
        }
    }
};

// === MODULE 3: QR CODE EXTRACTOR ===
const QrAnswerExtractor = {
    // ... Copy toàn bộ nội dung của QrAnswerExtractor vào đây (từ _xoaNoiDung đến hết showModal) ...
};

// === MODULE 4: GÁN ID ===
// ... Copy toàn bộ nội dung của file ganID.js của bạn vào đây ...
// Nhớ bọc nó trong một đối tượng hoặc một hàm init để tránh xung đột
const GanID = {
    init() {
        // Code trong `DOMContentLoaded` của file ganID.js sẽ được đặt ở đây
    }
};


// === HÀM KHỞI CHẠY CHÍNH CỦA ỨNG DỤNG ===
const App = {
    editor: null, // Biến để lưu trữ instance của editor

    init() {
        // Lấy các element DOM
        const compileBtn = document.getElementById('compile-btn');
        //... các element khác

        // Cấu hình Monaco Editor
        require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.34.0/min/vs' }});
        require(['vs/editor/editor.main'], (monaco) => {
            this.editor = monaco.editor.create(document.getElementById('editor'), {
                //... cấu hình editor ...
            });

            // Sau khi editor đã sẵn sàng, gán tất cả các sự kiện
            this.setupEventListeners();
        });
        
        // Khởi tạo các module khác không phụ thuộc editor
        GanID.init();
    },

    setupEventListeners() {
        if (!this.editor) return;
        
        // Gắn sự kiện cho các nút
        document.getElementById('compile-btn').addEventListener('click', () => this.compileLatex());
        document.getElementById('snippet-manager-btn').addEventListener('click', () => SnippetManager.show(this.editor));
        document.getElementById('code-tools-btn').addEventListener('click', () => CodeTools.showModal(this.editor));
        document.getElementById('qr-tool-btn').addEventListener('click', () => QrAnswerExtractor.showModal(this.editor));
        // ... các event listener khác ...

        this.editor.addAction({ id: 'compile-action', label: 'Compile', keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS], run: () => this.compileLatex() });
    },

    async compileLatex() {
        // ... nội dung hàm compileLatex không đổi ...
    }
};

// Đợi trang tải xong rồi mới chạy ứng dụng chính
document.addEventListener('DOMContentLoaded', () => App.init());