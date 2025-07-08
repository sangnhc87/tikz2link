// static/code_tools.js
const CodeTools = {
    beautifyLatexCode(content) {
    // === DANH SÁCH CÁC MÔI TRƯỜNG LUÔN SÁT LỀ ===
    const topLevelEnvs = ['ex', 'vd', 'bt']; 

    const indent = '    '; // 4 dấu cách
    const lines = content.split('\n');
    let beautifiedLines = [];
    
    // Cờ để biết chúng ta có đang ở bên trong một môi trường "top-level" hay không
    let inTopLevelEnvironment = false;

    for (let line of lines) {
        line = line.trim();
        if (!line) continue; // Bỏ qua dòng trống

        const beginMatch = line.match(/\\begin\{([a-zA-Z*]+)\}/);
        const endMatch = line.match(/\\end\{([a-zA-Z*]+)\}/);

        if (beginMatch) {
            const envName = beginMatch[1];
            // Nếu đây là một môi trường top-level
            if (topLevelEnvs.includes(envName)) {
                beautifiedLines.push(line); // Thêm dòng \begin sát lề
                inTopLevelEnvironment = true;
            } else {
                // Nếu là môi trường khác, thụt lề nếu nó nằm trong môi trường top-level
                beautifiedLines.push((inTopLevelEnvironment ? indent : '') + line);
            }
        } else if (endMatch) {
            const envName = endMatch[1];
            // Nếu đây là môi trường top-level
            if (topLevelEnvs.includes(envName)) {
                beautifiedLines.push(line); // Thêm dòng \end sát lề
                inTopLevelEnvironment = false;
            } else {
                // Nếu là môi trường khác, thụt lề nếu nó nằm trong môi trường top-level
                beautifiedLines.push((inTopLevelEnvironment ? indent : '') + line);
            }
        } else {
            // Nếu là một dòng nội dung bình thường
            if (inTopLevelEnvironment) {
                beautifiedLines.push(indent + line); // Thụt lề nếu ở trong môi trường top-level
            } else {
                beautifiedLines.push(line); // Giữ nguyên nếu ở ngoài
            }
        }
    }
    return beautifiedLines.join('\n');
},
numberQuestions(text, selectedEnvs, startNumber) {
    let questionCounters = {};
    selectedEnvs.forEach(env => {
        questionCounters[env] = startNumber;
    });

    const lines = text.split('\n');
    const processedLines = lines.map(line => {
        const beginEnvMatch = line.match(/\\begin\{(\w+)\}/);
        if (beginEnvMatch) {
            const envType = beginEnvMatch[1];
            if (selectedEnvs.includes(envType)) {
                const currentNumber = questionCounters[envType]++;
                return `%%========== Câu ${currentNumber} (${envType}) ==========\n${line}`;
            }
        }
        return line;
    });
    return processedLines.join('\n');
},
    removeLatexComments(text) {
    return text.split('\n')
               .filter(line => !line.trim().startsWith('%'))
               .join('\n');
},
    async showModal(editorInstance) { // Nhận editor của Monaco
        const { value: formValues } = await Swal.fire({
            title: 'Công cụ xử lý LaTeX',
            html: `
                <div id="latex-tools-form" style="text-align: left; font-size: 1em;">
                    <div class="form-check"><input class="form-check-input" type="checkbox" id="tool-beautify"><label for="tool-beautify"><strong>Làm đẹp Code</strong></label></div>
                    <div class="form-check"><input class="form-check-input" type="checkbox" id="tool-remove-comments"><label for="tool-remove-comments"><strong>Xóa Comments (%)</strong></label></div>
                    <hr><div class="form-check"><input class="form-check-input" type="checkbox" id="tool-numbering-toggle"><label for="tool-numbering-toggle"><strong>Đánh số câu hỏi...</strong></label></div>
                    <div id="numbering-options" style="display: none; padding-left: 25px; margin-top: 10px;">
                        <input type="text" id="tool-envs" class="swal2-input" placeholder="Môi trường, vd: ex,vd,bt" value="ex,vd,bt">
                        <input type="number" id="tool-start-number" class="swal2-input" placeholder="Số bắt đầu" value="1">
                    </div>
                </div>`,
            confirmButtonText: 'Thực hiện', showCancelButton: true, focusConfirm: false,
            didOpen: () => {
                document.getElementById('tool-numbering-toggle').addEventListener('change', (e) => {
                    document.getElementById('numbering-options').style.display = e.target.checked ? 'block' : 'none';
                });
            },
            preConfirm: () => ({
                beautify: document.getElementById('tool-beautify').checked,
                removeComments: document.getElementById('tool-remove-comments').checked,
                doNumbering: document.getElementById('tool-numbering-toggle').checked,
                envs: document.getElementById('tool-envs').value.split(',').map(e => e.trim()).filter(Boolean),
                startNumber: parseInt(document.getElementById('tool-start-number').value, 10) || 1
            })
        });
        if (formValues) {
            let content = editorInstance.getValue(); // Dùng editor của Monaco
            if (formValues.doNumbering && formValues.envs.length > 0) {
                content = this.numberQuestions(content, formValues.envs, formValues.startNumber);
            }
            if (formValues.removeComments) {
                content = this.removeLatexComments(content);
            }
            if (formValues.beautify) {
                content = this.beautifyLatexCode(content);
            }
            editorInstance.setValue(content); // Cập nhật nội dung cho Monaco
            Swal.fire('Hoàn thành!', 'Đã áp dụng các thay đổi.', 'success');
        }
    }
};