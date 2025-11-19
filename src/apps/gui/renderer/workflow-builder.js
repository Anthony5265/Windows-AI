/**
 * Windows AI - Enhanced Visual Workflow Builder
 * Modern drag-and-drop workflow creation interface
 */

class WorkflowBuilder {
    constructor() {
        this.nodes = new Map();
        this.connections = [];
        this.selectedNode = null;
        this.draggedNode = null;
        this.connecting = null;
        this.nodeCounter = 0;
        this.zoom = 1;
        this.pan = { x: 0, y: 0 };
        this.clipboard = null;

        this.canvas = document.getElementById('canvas');
        this.connectionLayer = document.getElementById('connectionLayer');
        this.propertiesContent = document.getElementById('propertiesContent');
        this.statusText = document.getElementById('statusText');
        this.nodeCount = document.getElementById('nodeCount');
        this.notification = document.getElementById('notification');
        this.contextMenu = document.getElementById('contextMenu');

        this.initEventListeners();
        this.updateConnectionLayerSize();
    }

    initEventListeners() {
        // Drag and drop from palette
        document.querySelectorAll('.node-template').forEach(template => {
            template.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('nodeType', template.dataset.type);
            });
        });

        this.canvas.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        this.canvas.addEventListener('drop', (e) => {
            e.preventDefault();
            const nodeType = e.dataTransfer.getData('nodeType');
            if (nodeType) {
                const rect = this.canvas.getBoundingClientRect();
                const x = (e.clientX - rect.left) / this.zoom - this.pan.x;
                const y = (e.clientY - rect.top) / this.zoom - this.pan.y;
                this.createNode(nodeType, x, y);
            }
        });

        // Canvas click (deselect)
        this.canvas.addEventListener('click', (e) => {
            if (e.target === this.canvas) {
                this.deselectAllNodes();
            }
        });

        // Context menu
        this.canvas.addEventListener('contextmenu', (e) => {
            if (e.target.closest('.workflow-node')) {
                e.preventDefault();
                this.showContextMenu(e.clientX, e.clientY);
            }
        });

        document.addEventListener('click', () => {
            this.contextMenu.style.display = 'none';
        });

        this.contextMenu.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            if (action && this.selectedNode) {
                this.handleContextAction(action);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveWorkflow();
            } else if (e.key === 'Delete' && this.selectedNode) {
                this.deleteNode(this.selectedNode);
            } else if (e.ctrlKey && e.key === 'c' && this.selectedNode) {
                this.copyNode();
            } else if (e.ctrlKey && e.key === 'v' && this.clipboard) {
                this.pasteNode();
            } else if (e.ctrlKey && e.key === 'd' && this.selectedNode) {
                e.preventDefault();
                this.duplicateNode(this.selectedNode);
            }
        });

        // Toolbar buttons
        document.getElementById('newWorkflowBtn').addEventListener('click', () => this.newWorkflow());
        document.getElementById('saveWorkflowBtn').addEventListener('click', () => this.saveWorkflow());
        document.getElementById('loadWorkflowBtn').addEventListener('click', () => this.loadWorkflow());
        document.getElementById('executeWorkflowBtn').addEventListener('click', () => this.executeWorkflow());

        // Zoom controls
        document.getElementById('zoomInBtn').addEventListener('click', () => this.setZoom(this.zoom + 0.1));
        document.getElementById('zoomOutBtn').addEventListener('click', () => this.setZoom(this.zoom - 0.1));
        document.getElementById('zoomResetBtn').addEventListener('click', () => this.setZoom(1));

        // Window resize
        window.addEventListener('resize', () => this.updateConnectionLayerSize());
    }

    createNode(type, x, y) {
        const nodeId = `node_${this.nodeCounter++}`;
        const nodeEl = document.createElement('div');
        nodeEl.className = 'workflow-node';
        nodeEl.dataset.nodeId = nodeId;
        nodeEl.style.left = `${x}px`;
        nodeEl.style.top = `${y}px`;

        const nodeConfig = this.getNodeConfig(type);

        nodeEl.innerHTML = `
            <div class="node-header">
                <div class="node-title">${nodeConfig.icon} ${nodeConfig.title}</div>
                <button class="node-delete">×</button>
            </div>
            <div class="node-content">${nodeConfig.description}</div>
            <div class="node-ports">
                <div class="port port-in" data-port="in"></div>
                <div class="port port-out" data-port="out"></div>
            </div>
        `;

        // Node data
        const nodeData = {
            id: nodeId,
            type: type,
            x: x,
            y: y,
            properties: { ...nodeConfig.defaultProperties }
        };

        this.nodes.set(nodeId, nodeData);
        this.canvas.appendChild(nodeEl);

        // Event listeners
        this.setupNodeEvents(nodeEl, nodeId);

        this.updateStatus();
        this.showNotification(`Added ${nodeConfig.title} node`);

        return nodeId;
    }

    getNodeConfig(type) {
        const configs = {
            action: {
                icon: '⚡',
                title: 'Action',
                description: 'Execute command',
                defaultProperties: {
                    command: '',
                    parameters: '',
                    timeout: 30
                }
            },
            condition: {
                icon: '🔀',
                title: 'Condition',
                description: 'Branch logic',
                defaultProperties: {
                    condition: '',
                    trueAction: '',
                    falseAction: ''
                }
            },
            loop: {
                icon: '🔄',
                title: 'Loop',
                description: 'Repeat actions',
                defaultProperties: {
                    iterations: 1,
                    condition: ''
                }
            },
            trigger: {
                icon: '▶️',
                title: 'Trigger',
                description: 'Workflow start',
                defaultProperties: {
                    event: 'manual',
                    schedule: ''
                }
            },
            delay: {
                icon: '⏱️',
                title: 'Delay',
                description: 'Wait period',
                defaultProperties: {
                    duration: 1000,
                    unit: 'milliseconds'
                }
            },
            ai: {
                icon: '🤖',
                title: 'AI Task',
                description: 'AI processing',
                defaultProperties: {
                    model: 'gpt-4',
                    prompt: '',
                    temperature: 0.7
                }
            },
            notification: {
                icon: '🔔',
                title: 'Notification',
                description: 'User alert',
                defaultProperties: {
                    message: '',
                    priority: 'normal'
                }
            },
            data: {
                icon: '📊',
                title: 'Data',
                description: 'Data transform',
                defaultProperties: {
                    operation: 'transform',
                    input: '',
                    output: ''
                }
            }
        };

        return configs[type] || configs.action;
    }

    setupNodeEvents(nodeEl, nodeId) {
        // Select node
        nodeEl.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectNode(nodeId);
        });

        // Drag node
        let isDragging = false;
        let dragStart = { x: 0, y: 0 };

        nodeEl.addEventListener('mousedown', (e) => {
            if (e.target.closest('.port') || e.target.classList.contains('node-delete')) {
                return;
            }

            isDragging = true;
            nodeEl.classList.add('dragging');
            dragStart = {
                x: e.clientX - parseInt(nodeEl.style.left),
                y: e.clientY - parseInt(nodeEl.style.top)
            };
        });

        document.addEventListener('mousemove', (e) => {
            if (isDragging) {
                const x = e.clientX - dragStart.x;
                const y = e.clientY - dragStart.y;
                nodeEl.style.left = `${x}px`;
                nodeEl.style.top = `${y}px`;

                this.nodes.get(nodeId).x = x;
                this.nodes.get(nodeId).y = y;

                this.updateConnections();
            }
        });

        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                nodeEl.classList.remove('dragging');
            }
        });

        // Delete button
        nodeEl.querySelector('.node-delete').addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteNode(nodeId);
        });

        // Port connections
        const ports = nodeEl.querySelectorAll('.port');
        ports.forEach(port => {
            port.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                this.startConnection(nodeId, port.dataset.port);
            });

            port.addEventListener('mouseup', (e) => {
                e.stopPropagation();
                this.endConnection(nodeId, port.dataset.port);
            });
        });
    }

    selectNode(nodeId) {
        this.deselectAllNodes();
        this.selectedNode = nodeId;

        const nodeEl = document.querySelector(`[data-node-id="${nodeId}"]`);
        if (nodeEl) {
            nodeEl.classList.add('selected');
        }

        this.showProperties(nodeId);
    }

    deselectAllNodes() {
        document.querySelectorAll('.workflow-node').forEach(node => {
            node.classList.remove('selected');
        });
        this.selectedNode = null;
        this.propertiesContent.innerHTML = '<p style="color: #666;">Select a node to edit its properties</p>';
    }

    showProperties(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node) return;

        let html = `<div class="property-group">
            <label class="property-label">Node ID</label>
            <input class="property-input" value="${node.id}" disabled>
        </div>`;

        html += `<div class="property-group">
            <label class="property-label">Node Type</label>
            <input class="property-input" value="${node.type}" disabled>
        </div>`;

        Object.entries(node.properties).forEach(([key, value]) => {
            html += `<div class="property-group">
                <label class="property-label">${key.replace(/([A-Z])/g, ' $1').trim()}</label>
                <input class="property-input" data-property="${key}" value="${value}">
            </div>`;
        });

        this.propertiesContent.innerHTML = html;

        // Property change listeners
        this.propertiesContent.querySelectorAll('[data-property]').forEach(input => {
            input.addEventListener('input', (e) => {
                const property = e.target.dataset.property;
                node.properties[property] = e.target.value;
                this.showNotification(`Updated ${property}`);
            });
        });
    }

    deleteNode(nodeId) {
        const nodeEl = document.querySelector(`[data-node-id="${nodeId}"]`);
        if (nodeEl) {
            nodeEl.remove();
        }

        this.nodes.delete(nodeId);

        // Remove connections
        this.connections = this.connections.filter(
            conn => conn.from !== nodeId && conn.to !== nodeId
        );

        this.updateConnections();
        this.updateStatus();
        this.showNotification('Node deleted');
    }

    duplicateNode(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node) return;

        this.createNode(node.type, node.x + 50, node.y + 50);
    }

    copyNode() {
        if (this.selectedNode) {
            this.clipboard = JSON.parse(JSON.stringify(this.nodes.get(this.selectedNode)));
            this.showNotification('Node copied');
        }
    }

    pasteNode() {
        if (this.clipboard) {
            const newId = this.createNode(this.clipboard.type, this.clipboard.x + 50, this.clipboard.y + 50);
            const newNode = this.nodes.get(newId);
            newNode.properties = { ...this.clipboard.properties };
            this.showNotification('Node pasted');
        }
    }

    startConnection(nodeId, portType) {
        if (portType === 'out') {
            this.connecting = { from: nodeId };
        }
    }

    endConnection(nodeId, portType) {
        if (this.connecting && portType === 'in') {
            this.connections.push({
                from: this.connecting.from,
                to: nodeId
            });
            this.updateConnections();
            this.showNotification('Connection created');
        }
        this.connecting = null;
    }

    updateConnections() {
        // Clear existing connections
        this.connectionLayer.innerHTML = '';

        this.connections.forEach(conn => {
            const fromNode = document.querySelector(`[data-node-id="${conn.from}"]`);
            const toNode = document.querySelector(`[data-node-id="${conn.to}"]`);

            if (fromNode && toNode) {
                const fromPort = fromNode.querySelector('.port-out');
                const toPort = toNode.querySelector('.port-in');

                const fromRect = fromPort.getBoundingClientRect();
                const toRect = toPort.getBoundingClientRect();
                const canvasRect = this.canvas.getBoundingClientRect();

                const x1 = fromRect.left + fromRect.width / 2 - canvasRect.left;
                const y1 = fromRect.top + fromRect.height / 2 - canvasRect.top;
                const x2 = toRect.left + toRect.width / 2 - canvasRect.left;
                const y2 = toRect.top + toRect.height / 2 - canvasRect.top;

                const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                const d = `M ${x1} ${y1} C ${x1 + 100} ${y1}, ${x2 - 100} ${y2}, ${x2} ${y2}`;
                line.setAttribute('d', d);
                line.setAttribute('stroke', '#0078d4');
                line.setAttribute('stroke-width', '2');
                line.setAttribute('fill', 'none');

                this.connectionLayer.appendChild(line);
            }
        });
    }

    updateConnectionLayerSize() {
        const rect = this.canvas.getBoundingClientRect();
        this.connectionLayer.setAttribute('width', rect.width);
        this.connectionLayer.setAttribute('height', rect.height);
        this.updateConnections();
    }

    setZoom(zoom) {
        this.zoom = Math.max(0.25, Math.min(2, zoom));
        this.canvas.style.transform = `scale(${this.zoom})`;
        this.updateStatus();
    }

    showNotification(message) {
        this.notification.textContent = message;
        this.notification.classList.add('show');
        setTimeout(() => {
            this.notification.classList.remove('show');
        }, 2000);
    }

    showContextMenu(x, y) {
        this.contextMenu.style.left = `${x}px`;
        this.contextMenu.style.top = `${y}px`;
        this.contextMenu.style.display = 'block';
    }

    handleContextAction(action) {
        switch (action) {
            case 'delete':
                this.deleteNode(this.selectedNode);
                break;
            case 'duplicate':
                this.duplicateNode(this.selectedNode);
                break;
            case 'copy':
                this.copyNode();
                break;
            case 'paste':
                this.pasteNode();
                break;
        }
    }

    updateStatus() {
        this.statusText.textContent = `Zoom: ${Math.round(this.zoom * 100)}%`;
        this.nodeCount.textContent = `${this.nodes.size} nodes, ${this.connections.length} connections`;
    }

    newWorkflow() {
        if (confirm('Create new workflow? Unsaved changes will be lost.')) {
            this.canvas.innerHTML = '';
            this.nodes.clear();
            this.connections = [];
            this.nodeCounter = 0;
            this.updateStatus();
            this.showNotification('New workflow created');
        }
    }

    async saveWorkflow() {
        const workflow = {
            version: '1.0',
            nodes: Array.from(this.nodes.values()),
            connections: this.connections
        };

        try {
            // Use Electron IPC to save
            const result = await window.electronAPI?.invoke('save-workflow', workflow);
            if (result) {
                this.showNotification('Workflow saved successfully');
            }
        } catch (error) {
            console.error('Save failed:', error);
            this.showNotification('Save failed');
        }
    }

    async loadWorkflow() {
        try {
            const workflow = await window.electronAPI?.invoke('load-workflow');
            if (workflow) {
                this.canvas.innerHTML = '';
                this.nodes.clear();
                this.connections = [];

                workflow.nodes.forEach(node => {
                    this.nodes.set(node.id, node);
                    this.createNodeElement(node);
                });

                this.connections = workflow.connections;
                this.updateConnections();
                this.updateStatus();
                this.showNotification('Workflow loaded');
            }
        } catch (error) {
            console.error('Load failed:', error);
            this.showNotification('Load failed');
        }
    }

    async executeWorkflow() {
        const workflow = {
            nodes: Array.from(this.nodes.values()),
            connections: this.connections
        };

        try {
            this.showNotification('Executing workflow...');
            const result = await window.electronAPI?.invoke('execute-workflow', workflow);
            if (result.success) {
                this.showNotification('Workflow executed successfully');
            } else {
                this.showNotification(`Execution failed: ${result.error}`);
            }
        } catch (error) {
            console.error('Execution failed:', error);
            this.showNotification('Execution failed');
        }
    }

    createNodeElement(node) {
        const nodeEl = document.createElement('div');
        nodeEl.className = 'workflow-node';
        nodeEl.dataset.nodeId = node.id;
        nodeEl.style.left = `${node.x}px`;
        nodeEl.style.top = `${node.y}px`;

        const nodeConfig = this.getNodeConfig(node.type);

        nodeEl.innerHTML = `
            <div class="node-header">
                <div class="node-title">${nodeConfig.icon} ${nodeConfig.title}</div>
                <button class="node-delete">×</button>
            </div>
            <div class="node-content">${nodeConfig.description}</div>
            <div class="node-ports">
                <div class="port port-in" data-port="in"></div>
                <div class="port port-out" data-port="out"></div>
            </div>
        `;

        this.canvas.appendChild(nodeEl);
        this.setupNodeEvents(nodeEl, node.id);
    }
}

// Initialize workflow builder
const workflowBuilder = new WorkflowBuilder();
