// static/snippets.js
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
            const response = await fetch('/static/snippets.json');
            if (!response.ok) throw new Error('Không thể tải file snippets.json');
            const snippetsData = await response.json();
            const treeHtml = this._buildTreeHtml(snippetsData);
            
            Swal.fire({
                title: '<strong>Kho Snippet</strong>',
                html: `<div id="snippet-tree-container">${treeHtml}</div>`,
                width: '600px', showCloseButton: true, showConfirmButton: false,
                didOpen: () => {
                    const container = document.getElementById('snippet-tree-container');
                    container.addEventListener('click', (e) => {
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