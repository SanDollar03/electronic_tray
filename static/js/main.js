// static/js/main.js
// 担当者管理 + 添付ファイルプレビュー

document.addEventListener('DOMContentLoaded', () => {

    /* ========== 担当者ロジック ========== */
    const input = document.getElementById('assigneeInput');
    const addBtn = document.getElementById('addAssigneeBtn');
    const listUI = document.getElementById('selectedAssignees');
    const hiddenSel = document.getElementById('assigneeHidden');
    const MAX_A = 10;

    function syncHidden() {
        hiddenSel.innerHTML = '';
        [...listUI.children].forEach(li =>
            hiddenSel.insertAdjacentHTML(
                'beforeend',
                `<option value="${li.dataset.uid}" selected></option>`
            )
        );
    }
    function addAssignee() {
        const text = input.value.trim();
        if (!text) return;

        const user = userMap.find(u =>
            (`${u.display_name} (${u.email})`).toLowerCase() === text.toLowerCase()
        );
        if (!user) { alert('ユーザーが見つかりません'); return; }
        if ([...listUI.children].some(li => li.dataset.uid === user.id)) {
            alert('既に追加済みです'); return;
        }
        if (listUI.children.length >= MAX_A) {
            alert(`担当者は最大 ${MAX_A} 名までです`); return;
        }

        const li = document.createElement('li');
        li.dataset.uid = user.id;
        li.textContent = text + ' ';
        const del = document.createElement('button');
        del.type = 'button';
        del.textContent = '✕';
        del.className = 'btn small';
        del.onclick = () => { li.remove(); syncHidden(); };
        li.appendChild(del);
        listUI.appendChild(li);

        syncHidden();
        input.value = '';
        input.focus();
    }
    addBtn.addEventListener('click', addAssignee);
    input.addEventListener('keydown', e => {
        if (e.key === 'Enter') { e.preventDefault(); addAssignee(); }
    });

    /* ========== 添付ファイルロジック ========== */
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const MAX_F = 10;
    let filesArr = [];

    function rebuildInput() {
        const dt = new DataTransfer();
        filesArr.forEach(f => dt.items.add(f));
        fileInput.files = dt.files;
    }
    function redrawFiles() {
        fileList.innerHTML = '';
        filesArr.forEach((f, i) => {
            const li = document.createElement('li');
            li.textContent = `${i + 1}. ${f.name} `;
            const del = document.createElement('button');
            del.type = 'button';
            del.textContent = '✕';
            del.className = 'btn small';
            del.onclick = () => {
                filesArr = filesArr.filter(x => x !== f);
                redrawFiles();
                rebuildInput();
            };
            li.appendChild(del);
            fileList.appendChild(li);
        });
    }
    fileInput.addEventListener('change', () => {
        Array.from(fileInput.files).forEach(f => {
            if (!filesArr.some(x => x.name === f.name)) filesArr.push(f);
        });
        if (filesArr.length > MAX_F) {
            alert(`添付は最大 ${MAX_F} 件までです`);
            filesArr = filesArr.slice(0, MAX_F);
        }
        redrawFiles();
        rebuildInput();
    });

});
