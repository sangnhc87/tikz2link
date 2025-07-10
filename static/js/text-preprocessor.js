// File: static/js/text-preprocessor.js
// PHIÊN BẢN ĐƠN GIẢN HÓA VÀ ĐÁNG TIN CẬY

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

    /**
     * Hàm xử lý chính, nhận văn bản và bộ quy tắc.
     * @param {string} text - Văn bản LaTeX đầu vào.
     * @param {object} rules - Đối tượng chứa các quy tắc thay thế.
     * @returns {string} - Văn bản đã được xử lý.
     */
    function _process(text, rules) {
        if (!rules) {
            console.warn("Text Preprocessor: Không có quy tắc nào được cung cấp.");
            return text;
        }
        
        let processedText = text;

        // BƯỚC 1: Xử lý các thay thế đơn giản (Simple Replacements)
        // Đây là nơi `[thm]` và `eqnarray*` của bạn được xử lý.
        if (rules.simpleReplacements) {
            for (const [find, replace] of Object.entries(rules.simpleReplacements)) {
                // Phải thoát các ký tự đặc biệt trong 'find' để tạo regex
                const escapedFind = find.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                processedText = processedText.replace(new RegExp(escapedFind, 'g'), replace);
            }
        }
        
        // BƯỚC 2: Xử lý các lệnh có tham số (Command Replacements)
        if (rules.commandReplacements) {
            for (const [command, config] of Object.entries(rules.commandReplacements)) {
                const { start: startTag, end: endTag } = config;
                const commandRegex = new RegExp(`\\\\${command}\\s*\\{`, 'g');
                
                let tempResult = "";
                let lastIndex = 0;
                let match;

                // Thao tác trên một bản sao để tránh lỗi
                const currentText = processedText; 
                
                while ((match = commandRegex.exec(currentText)) !== null) {
                    const openBraceIndex = commandRegex.lastIndex;
                    const closeBraceIndex = findMatchingBrace(currentText, openBraceIndex);
                    
                    if (closeBraceIndex !== -1) {
                        tempResult += currentText.substring(lastIndex, match.index);
                        const content = currentText.substring(openBraceIndex, closeBraceIndex);
                        tempResult += `${startTag}${content}${endTag}`;
                        lastIndex = closeBraceIndex + 1;
                        commandRegex.lastIndex = lastIndex;
                    } else {
                        commandRegex.lastIndex = openBraceIndex;
                    }
                }
                tempResult += currentText.substring(lastIndex);
                processedText = tempResult; // Cập nhật kết quả sau khi vòng lặp hoàn tất
            }
        }

        // BƯỚC 3: Xử lý các thay thế bằng Regex (Regex Replacements)
        // Đây là bước quan trọng cần phải hoạt động.
        if (rules.regexReplacements) {
            for (const rule of rules.regexReplacements) {
                try {
                    const regex = new RegExp(rule.find, rule.flags || 'g');
                    processedText = processedText.replace(regex, rule.replace);
                } catch (e) {
                    console.error(`Lỗi Regex trong file replace.json: `, rule.find, e);
                }
            }
        }
        
        // Lưu ý: environmentReplacements và tabular đã được loại bỏ theo yêu cầu của bạn.

        return processedText;
    }

    return {
        process: _process
    };

})();