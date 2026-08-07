    let renderedIds = new Set();
    const MAX_MESSAGES = 100;
    const chatEl = document.getElementById("chat");

    const PLACEHOLDER_URL = "/static/image.png";

    function colorFromUsername(name) {
        let hash = 0;
        const text = String(name || "").toLowerCase();
        for (let i = 0; i < text.length; i++) {
            hash = ((hash << 5) - hash) + text.charCodeAt(i);
            hash |= 0;
        }
        const hue = Math.abs(hash) % 360;
        return `hsl(${hue}, 75%, 65%)`;
    }

    function renderMessageText(text) {
        const raw = String(text ?? "");
        const urlRegex = /(https?:\/\/[^\s]+)/gi;
        let html = "";
        let lastIndex = 0;
        let match;
        const sanitize = (str) => {
            const div = document.createElement("div");
            div.textContent = str;
            return div.innerHTML;
        };

        while ((match = urlRegex.exec(raw)) !== null) {
            const url = match[0];
            html += sanitize(raw.slice(lastIndex, match.index));
            const safeUrl = encodeURI(url);
            html += `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer">${sanitize(url)}</a>`;
            
            html += `<img class="chat-image" src="${PLACEHOLDER_URL}" data-src="${safeUrl}" alt="chat image" loading="lazy">`;
            
            lastIndex = match.index + url.length;
        }
        html += sanitize(raw.slice(lastIndex));
        return html;
    }

    async function update() {
        try {
            const r = await fetch("/chatjson");
            const d = await r.json();
            
            const nearBottom = (chatEl.scrollHeight - chatEl.scrollTop - chatEl.clientHeight) < 100;
            let newMessagesAdded = false;

            d.messages.forEach(m => {
                if (!renderedIds.has(m.id)) {
                    newMessagesAdded = true;
                    const msgDiv = document.createElement("div");
                    msgDiv.className = "msg";
                    msgDiv.dataset.id = m.id;

                    const row = document.createElement("div");
                    row.className = "msg-row";

                    if (d.show_pfp) {
                        const img = document.createElement("img");
                        img.className = "msg-avatar";
                        img.src = m.pfp_url;
                        img.onerror = () => img.remove();
                        row.appendChild(img);
                    }

                    const content = document.createElement("div");
                    content.className = "msg-content";

                    let userColor = colorFromUsername(m.user);
                    if (m.is_owner) userColor = "#ffdf3a";
                    else if (m.is_moderator) userColor = "#50a5ff";

                    const userSpan = document.createElement("span");
                    userSpan.className = "user";
                    userSpan.style.color = userColor;
                    userSpan.textContent = m.user;
                    
                    content.appendChild(userSpan);
                    content.append(": ");

                    const textSpan = document.createElement("span");
                    textSpan.innerHTML = renderMessageText(m.text);
                    const imgs = textSpan.querySelectorAll("img");
                    imgs.forEach(img => {
                        const realSrc = img.dataset.src;
                        const actualImg = new Image();
                        
                        actualImg.onload = () => {
                            img.src = realSrc;
                            if (nearBottom) {
                                chatEl.scrollTop = chatEl.scrollHeight;
                            }
                        };
                        
                        actualImg.onerror = () => {
                            img.src = "/static/err.png";
                        };

                        actualImg.src = realSrc;
                    });

                    content.appendChild(textSpan);
                    row.appendChild(content);
                    msgDiv.appendChild(row);
                    chatEl.appendChild(msgDiv);
                    
                    renderedIds.add(m.id);
                }
            });

            while (chatEl.children.length > MAX_MESSAGES) {
                const oldest = chatEl.firstChild;
                renderedIds.delete(oldest.dataset.id);
                chatEl.removeChild(oldest);
            }

            if (nearBottom && newMessagesAdded) {
                chatEl.scrollTop = chatEl.scrollHeight;
            }
        } catch (e) {
            console.error("Chat update failed:", e);
        }
    }

    async function poll() {
        await update();
        setTimeout(poll, 1000);
    }
    poll();