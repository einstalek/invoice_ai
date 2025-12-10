HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python OCR Invoice Extractor</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';</script>
    <style>
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
        .highlight-box {
            position: absolute;
            background-color: rgba(59, 130, 246, 0.2);
            border: 2px solid #2563eb;
            transition: all 0.2s ease;
            pointer-events: none;
            z-index: 10;
        }
        .json-row:hover { background-color: #f8fafc; cursor: pointer; }
        .json-row.active { background-color: #eff6ff; border-left: 4px solid #2563eb; }
    </style>
</head>
<body class="bg-slate-50 h-screen flex flex-col overflow-hidden text-slate-800">

    <header class="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shrink-0">
        <div class="flex items-center gap-3">
            <h1 class="font-bold text-lg tracking-tight">OCR Extract <span class="font-normal text-slate-500">/ Python Server</span></h1>
        </div>
        <div id="status-indicator" class="hidden flex items-center gap-2 text-sm font-medium text-blue-600">
            Processing...
        </div>
        <button onclick="location.reload()" id="reset-btn" class="hidden px-4 py-2 text-sm text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
            Clear Session
        </button>
    </header>

    <main class="flex-1 flex overflow-hidden">
        <!-- Scrollable Container for PDF -->
        <!-- Fixed: Removed 'flex items-center' from parent to prevent scrolling issues. 
             Used 'block' display for reliable scrolling behavior. -->
        <div class="flex-1 bg-slate-100 relative overflow-auto border-r border-slate-200" id="pdf-wrapper">
            
            <!-- Drop Zone -->
            <!-- Added margin-top and auto margins to center it without flex parent -->
            <div id="drop-zone" class="max-w-md mx-auto mt-20 flex flex-col items-center justify-center p-12 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 hover:bg-white hover:border-blue-400 transition-all cursor-pointer">
                <p class="text-lg font-medium text-slate-600">Drop PDF Invoice here</p>
                <input type="file" id="file-input" class="hidden" accept="application/pdf">
            </div>

            <!-- Container for Multiple Pages -->
            <!-- Inner container handles the centering of the canvas elements -->
            <div id="canvas-container" class="hidden flex flex-col items-center gap-4 py-8 min-h-full w-full">
                <!-- Pages will be injected here by JS -->
            </div>
        </div>

        <div class="w-[450px] bg-white flex flex-col border-l border-slate-200 shadow-xl z-10" id="sidebar">
            <div class="p-4 border-b border-slate-100 bg-slate-50">
                <h2 class="font-semibold text-slate-700">Extracted Data</h2>
            </div>
            <div id="json-content" class="flex-1 overflow-y-auto p-2 space-y-1">
                <div class="h-full flex flex-col items-center justify-center text-slate-400 text-sm p-8 text-center">Waiting for document...</div>
            </div>
        </div>
    </main>

    <script>
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const statusIndicator = document.getElementById('status-indicator');
        const resetBtn = document.getElementById('reset-btn');
        const canvasContainer = document.getElementById('canvas-container');
        const jsonContent = document.getElementById('json-content');
        const pdfWrapper = document.getElementById('pdf-wrapper');
        
        let currentPdfDoc = null;
        let pageScale = 1.2; 

        dropZone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('border-blue-400'); });
        dropZone.addEventListener('dragleave', (e) => { e.preventDefault(); dropZone.classList.remove('border-blue-400'); });
        dropZone.addEventListener('drop', (e) => { e.preventDefault(); handleFiles(e.dataTransfer.files); });

        function handleFiles(files) {
            if (files.length > 0 && files[0].type === 'application/pdf') {
                uploadFile(files[0]);
                renderPDF(files[0]);
            } else { alert("Please upload a valid PDF file."); }
        }

        async function renderPDF(file) {
            const fileReader = new FileReader();
            fileReader.onload = async function() {
                const typedarray = new Uint8Array(this.result);
                currentPdfDoc = await pdfjsLib.getDocument(typedarray).promise;
                
                // Clear container and show it
                canvasContainer.innerHTML = '';
                canvasContainer.classList.remove('hidden');
                dropZone.classList.add('hidden');

                // FIX: Immediately scroll to top to prevent showing the "tail"
                pdfWrapper.scrollTop = 0;

                // Loop through all pages
                for (let pageNum = 1; pageNum <= currentPdfDoc.numPages; pageNum++) {
                    const page = await currentPdfDoc.getPage(pageNum);
                    const viewport = page.getViewport({ scale: pageScale });
                    
                    // Create a wrapper div for this page
                    const pageWrapper = document.createElement('div');
                    pageWrapper.className = 'relative shadow-lg bg-white';
                    pageWrapper.style.width = viewport.width + 'px';
                    pageWrapper.style.height = viewport.height + 'px';
                    
                    // Create Canvas
                    const canvas = document.createElement('canvas');
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    const ctx = canvas.getContext('2d');
                    
                    // Create Highlight Layer for this page
                    const highlightLayer = document.createElement('div');
                    highlightLayer.className = 'highlight-layer absolute inset-0';
                    highlightLayer.dataset.page = pageNum; 

                    pageWrapper.appendChild(canvas);
                    pageWrapper.appendChild(highlightLayer);
                    canvasContainer.appendChild(pageWrapper);
                    
                    // Render
                    await page.render({ canvasContext: ctx, viewport: viewport }).promise;
                }
            };
            fileReader.readAsArrayBuffer(file);
        }

        async function uploadFile(file) {
            const formData = new FormData();
            formData.append('file', file);
            statusIndicator.classList.remove('hidden');
            jsonContent.innerHTML = '<div class="p-8 text-center text-slate-500 animate-pulse">Extracting...</div>';

            try {
                const response = await fetch('/process', { method: 'POST', body: formData });
                const result = await response.json();
                displayJSON(result);
            } catch (error) {
                jsonContent.innerHTML = '<div class="text-red-500 p-4">Error processing file.</div>';
            } finally {
                statusIndicator.classList.add('hidden');
                resetBtn.classList.remove('hidden');
            }
        }

        function displayJSON(data) {
            jsonContent.innerHTML = '';
            Object.entries(data).forEach(([key, item]) => {
                const row = document.createElement('div');
                row.className = 'json-row p-3 rounded-lg mb-1 transition-colors border border-transparent';
                
                const value = typeof item === 'object' && item !== null ? item.value : item;
                const bbox = typeof item === 'object' && item !== null ? item.bbox : null;

                row.innerHTML = `
                    <div class="text-xs font-bold uppercase text-slate-400 tracking-wider mb-1">${key.replace(/_/g, ' ')}</div>
                    <div class="text-sm font-medium text-slate-800 break-words">${value || '<span class="text-slate-300 italic">Empty</span>'}</div>
                `;

                if (bbox) {
                    row.addEventListener('click', () => {
                        document.querySelectorAll('.json-row').forEach(r => r.classList.remove('active'));
                        row.classList.add('active');
                        drawHighlight(bbox);
                    });
                }
                jsonContent.appendChild(row);
            });
        }

        function drawHighlight(bbox) {
            // 1. Clear highlights on ALL pages
            document.querySelectorAll('.highlight-layer').forEach(el => el.innerHTML = '');
            
            if (!bbox) return;
            
            // 2. Determine which page to highlight. Default to Page 1.
            const pageNum = bbox.page || 1; 
            const targetLayer = document.querySelector(`.highlight-layer[data-page="${pageNum}"]`);
            
            if (targetLayer) {
                const div = document.createElement('div');
                div.className = 'highlight-box';
                // Expecting bbox as percentages [top, left, width, height]
                div.style.left = 100 * bbox[0] + '%';
                div.style.top = 100 * bbox[1] + '%';
                div.style.width = 100 * bbox[2] + '%';
                div.style.height = 100 * bbox[3] + '%';
                
                targetLayer.appendChild(div);
                
                // Scroll that page into view
                targetLayer.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    </script>
</body>
</html>
"""