// File: static/js/text-preprocessor.js
// PHIÊN BẢN HOÀN CHỈNH: Xử lý được cả eqnarray* và các bí danh của nó.

const TextPreprocessor = (function() {

    function findMatchingBrace(str, startPos) {
        let depth = 1;
        for (let i = startPos; i < str.length; i++) {
            if (str[i] === '{') depth++;
            else if (str[i] === '}') {
                depth--;
                if (depth === 0) return i;
            }
        }
        return -1;
    }

    function _process(text, rules) {
        if (!rules) {
            console.warn("Text Preprocessor: Không có quy tắc nào được cung cấp.");
            return text;
        }
        
        let processedText = text;

        if (rules.environmentReplacements) {
            for (const [envName, config] of Object.entries(rules.environmentReplacements)) {
                // Phải thoát các ký tự đặc biệt như '*' trong 'eqnarray*'
                const escapedEnvName = envName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const envRegex = new RegExp(`\\\\begin\\{${escapedEnvName}\\}([\\s\\S]*?)\\\\end\\{${escapedEnvName}\\}`, 'g');
                
                processedText = processedText.replace(envRegex, (match, content) => {
                    let newContent = content;
                    // Nếu quy tắc yêu cầu sửa nội dung (ví dụ: chuyển đổi từ cú pháp 3 cột của eqnarray)
                    if (config.fixContent) {
                        // Thay thế & ... & bằng & ...
                        newContent = newContent.replace(/&\s*([^&]*?)\s*&/g, '&$1');
                    }
                    // Trả về môi trường mục tiêu (ví dụ: aligned)
                    return `\\begin{${config.target}}${newContent}\\end{${config.target}}`;
                });
            }
        }

        if (rules.commandReplacements) {
            for (const [command, config] of Object.entries(rules.commandReplacements)) {
                const { start: startTag, end: endTag } = config;
                const commandToFind = `\\${command}{`;
                let result = "";
                let lastIndex = 0;
                let tempText = processedText;

                while (true) {
                    const commandIndex = tempText.indexOf(commandToFind, lastIndex);
                    if (commandIndex === -1) break;
                    const openBraceIndex = commandIndex + commandToFind.length;
                    const closeBraceIndex = findMatchingBrace(tempText, openBraceIndex);
                    if (closeBraceIndex === -1) {
                        lastIndex = openBraceIndex; continue;
                    }
                    const content = tempText.substring(openBraceIndex, closeBraceIndex);
                    result += tempText.substring(lastIndex, commandIndex);
                    result += `${startTag}${content}${endTag}`;
                    lastIndex = closeBraceIndex + 1;
                }
                result += tempText.substring(lastIndex);
                processedText = result;
            }
        }

        if (rules.simpleReplacements) {
            for (const [find, replace] of Object.entries(rules.simpleReplacements)) {
                const escapedFind = find.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                processedText = processedText.replace(new RegExp(escapedFind, 'g'), replace);
            }
        }
        
        return processedText;
    }

    return {
        process: _process
    };

})();