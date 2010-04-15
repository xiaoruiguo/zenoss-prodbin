/*
###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2010, Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################
*/

(function(){

var router, getSelectedTemplate, getSelectedGraphDefinition,
    addGraphDefinition, deleteGraphDefinition, addThresholdToGraph;


Ext.ns('Zenoss', 'Zenoss.templates');

router = Zenoss.remote.TemplateRouter;

getSelectedTemplate = function() {
    return Ext.getCmp('templateTree').getSelectionModel().getSelectedNode();
};

getSelectedGraphDefinition = function() {
    return Ext.getCmp('graphGrid').getSelectionModel().getSelected();
};

function getSelectedGraphPoint() {
    var cmp = Ext.getCmp('graphPointGrid');
    if (cmp) {
        return cmp.getSelectionModel().getSelected();
    }
    return null;
}

addGraphDefinition = function(){
    var params, callback;
    params = {
        templateUid: getSelectedTemplate().attributes.uid,
        graphDefinitionId: Ext.getCmp('graphDefinitionIdTextfield').getValue()
    };
    callback = function(provider, response) {
        Ext.getCmp('graphGrid').getStore().reload();
    };
    router.addGraphDefinition(params, callback);
};

new Zenoss.HideFormDialog({
    id: 'addGraphDefinitionDialog',
    title: _t('Add Graph Definition'),
    items: [
        {
            xtype: 'textfield',
            id: 'graphDefinitionIdTextfield',
            fieldLabel: _t('ID'),
            allowBlank: false,
            listeners: {
                invalid: function(){
                    Ext.getCmp('addGraphDefinitionSubmit').disable();
                },
                valid: function(){
                    Ext.getCmp('addGraphDefinitionSubmit').enable();
                }
            }
        }
    ],
    listeners: {
        hide: function() {
            Ext.getCmp('graphDefinitionIdTextfield').reset();
        }
    },
    buttons: [
    {
        xtype: 'HideDialogButton',
        id: 'addGraphDefinitionSubmit',
        text: _t('Submit'),
        disabled: true,
        handler: function(button, event) {
            addGraphDefinition();
        }
    }, {
        xtype: 'HideDialogButton',
        text: _t('Cancel')
    }]
});

deleteGraphDefinition = function() {
    var params, callback;
    params = {
        uid: getSelectedGraphDefinition().id
    };
    callback = function(provider, response) {
        Ext.getCmp('deleteGraphDefinitionButton').disable();
        Ext.getCmp('graphDefinitionMenuButton').disable();
        Ext.getCmp('graphGrid').getStore().reload();
    };
    router.deleteGraphDefinition(params, callback);
};


new Zenoss.MessageDialog({
    id: 'deleteGraphDefinitionDialog',
    title: _t('Delete Graph Definition'),
    // the message is generated dynamically
    okHandler: function(){
        deleteGraphDefinition();
    }
});

/**
 * Deletes the selected graph point
 **/
function deleteGraphPoint() {
    var params, callback;
    params = {
        uid: getSelectedGraphPoint().id
    };
    callback = function(provider, response) {
        Ext.getCmp('deleteGraphPointButton').disable();
        Ext.getCmp('editGraphPointButton').disable();
        Ext.getCmp('graphPointGrid').getStore().reload();
    };
    router.deleteGraphPoint(params, callback);
}

new Zenoss.MessageDialog({
    id: 'deleteGraphPointDialog',
    title: _t('Delete Graph Point'),
    // the message is generated dynamically
    okHandler: deleteGraphPoint
});
     
     
new Zenoss.MessageDialog({
    id: 'addDataPointToGraphDialog',
    title: _t('Add Data Point'),
    message: 'Not implemented yet.'
});

addThresholdToGraph = function() {
    var params, callback;
    params = {
        graphUid: getSelectedGraphDefinition().id,
        thresholdUid: Ext.getCmp('addThresholdToGraphCombo').getValue()
    };
    callback = function() {
        Ext.getCmp('graphPointGrid').getStore().reload();
    };
    router.addThresholdToGraph(params, callback);
};

new Zenoss.HideFormDialog({
    id: 'addThresholdToGraphDialog',
    title: _t('Add Threshold'),
    items: {
        xtype: 'combo',
        id: 'addThresholdToGraphCombo',
        fieldLabel: _t('Threshold'),
        valueField: 'uid',
        displayField: 'name',
        triggerAction: 'all',
        selectOnFocus: true,
        forceSelection: true,
        editable: false,
        allowBlank: false,
        listeners: {
            invalid: function(){
                Ext.getCmp('addThresholdToGraphSubmit').disable();
            },
            valid: function(){
                Ext.getCmp('addThresholdToGraphSubmit').enable();
            }
        },
        store: {
            xtype: 'directstore',
            directFn: router.getThresholds,
            fields: ['uid', 'name']
        }
    },
    listeners: {
        show: function() {
            var combo, uid;
            combo = Ext.getCmp('addThresholdToGraphCombo');
            combo.reset();
            Ext.getCmp('addThresholdToGraphSubmit').disable();
            uid = getSelectedTemplate().attributes.uid;
            combo.getStore().setBaseParam('uid', uid);
            delete combo.lastQuery;
            combo.doQuery(combo.allQuery, true);
        }
    },
    buttons: [
    {
        xtype: 'HideDialogButton',
        id: 'addThresholdToGraphSubmit',
        text: _t('Submit'),
        disabled: true,
        handler: function(button, event) {
            addThresholdToGraph();
        }
    }, {
        xtype: 'HideDialogButton',
        text: _t('Cancel')
    }]

});

new Zenoss.HideFormDialog({
    id: 'addCustomToGraphDialog',
    title: _t('Add Custom Graph Point'),
    listeners: {
        show: function(dialog) {
            dialog.idField.reset();
            dialog.typeCombo.reset();
            dialog._addButton.disable();
            delete dialog.typeCombo.lastQuery;
            dialog.typeCombo.doQuery(dialog.typeCombo.allQuery, true);
        }
    },
    items: [{
        xtype: 'textfield',
        ref: 'idField',
        fieldLabel: _t('ID'),
        allowBlank: false,
        listeners: {
            invalid: function(idField){
                idField.refOwner._addButton.disable();
            },
            valid: function(idField){
                if ( idField.refOwner.typeCombo.isValid(true) ) {
                    idField.refOwner._addButton.enable();
                }
            }
        }
    }, {
        xtype: 'combo',
        ref: 'typeCombo',
        fieldLabel: _t('Instruction Type'),
        valueField: 'pythonClassName',
        displayField: 'label',
        triggerAction: 'all',
        selectOnFocus: true,
        forceSelection: true,
        editable: false,
        allowBlank: false,
        listeners: {
            invalid: function(typeCombo){
                typeCombo.refOwner._addButton.disable();
            },
            valid: function(typeCombo){
                if ( typeCombo.refOwner.idField.isValid(true) ) {
                    typeCombo.refOwner._addButton.enable();
                }
            }
        },
        store: {
            xtype: 'directstore',
            directFn: router.getGraphInstructionTypes,
            fields: ['pythonClassName', 'label'],
            root: 'data'
        }
    }],
    buttons: [{
        xtype: 'HideDialogButton',
        ref: '../_addButton',
        text: _t('Add'),
        disabled: true,
        handler: function(addButton) {
            var params, callback;
            params = {
                graphUid: getSelectedGraphDefinition().id,
                customId: addButton.refOwner.idField.getValue(),
                customType: addButton.refOwner.typeCombo.getValue()
            };
            callback = function() {
                Ext.getCmp('graphPointGrid').getStore().reload();
            };
            router.addCustomToGraph(params, callback);
        }
    }, {
        xtype: 'HideDialogButton',
        ref: '../cancelButton',
        text: _t('Cancel')
    }]
});

/**********************************************************************
 *
 * Graph Custom Definition
 *
 */
Ext.create({
    xtype: 'window',
    title: _t('Graph Custom Definition'),
    id: 'graphCustomDefinitionDialog',
    closeAction: 'hide',
    buttonAlign: 'left',
    autoScroll: true,
    modal: true,
    plain: true,
    padding: 10,
    items: [{
        xtype:'form',
        ref: 'formPanel',
        labelAlign: 'top',
        border: false,
        monitorValid: true,
        paramsAsHash: true,
        api: {
            load: router.getGraphDefinition,
            submit: router.setInfo
        },
        items:[{
            xtype: 'label',
            fieldLabel: _t('Name'),
            name:'id',
            ref: 'nameLabel'
        },{
            xtype: 'textarea',
            fieldLabel: _t('Custom'),
            width: 500,
            height: 500,
            name: 'custom',
            ref: 'custom'
        },{
            xtype: 'label',
            fieldLabel: _t('Available RRD Variables'),
            border: false,
            ref: 'rrdVariables'
        }]
    }],
    buttons: [{
        xtype: 'HideDialogButton',
        text: _t('Submit'),
        handler: function(button, event) {
            var cmp = Ext.getCmp('graphCustomDefinitionDialog'),
                routerCallback,
                data = cmp.record,
                params = {};

            // we just need to update custom
            params.uid = data.uid;
            params.custom = cmp.formPanel.custom.getValue();

            router.setInfo(params);
        }
    }, {
        xtype: 'HideDialogButton',
        text: _t('Cancel')
    }],
    loadAndShow: function(uid) {
        this.uid = uid;
        this.formPanel.getForm().load({
            params: {uid:uid},
            success: function(btn, response) {
                var data = response.result.data;
                this.record = data;
                // populate the form
                this.formPanel.nameLabel.setText(data.id);
                this.formPanel.custom.setValue(data.custom);
                this.formPanel.rrdVariables.setText(data.rrdVariables.join('<br />'), false);

                this.show();
            },
            scope: this
        });
    }

});

Zenoss.GraphPointStore = Ext.extend(Ext.data.DirectStore, {
    constructor: function(config){
        Ext.applyIf(config, {
            directFn: router.getGraphPoints,
            idProperty: 'uid',
            fields: ['uid', 'name', 'type', 'description'],
            root: 'data'
        });
        Zenoss.GraphPointStore.superclass.constructor.call(this, config);
    }
});
Ext.reg('graphpointstore', Zenoss.GraphPointStore);

new Ext.menu.Menu({
    id: 'graphPointMenu',
    items: [{
        xtype: 'menuitem',
        text: _t('Data Point'),
        handler: function(){
            Ext.getCmp('addDataPointToGraphDialog').show();
        }
    }, {
        xtype: 'menuitem',
        text: _t('Threshold'),
        handler: function(){
            Ext.getCmp('addThresholdToGraphDialog').show();
        }
    }, {
        xtype: 'menuitem',
        text: _t('Custom Graph Point'),
        handler: function(){
            Ext.getCmp('addCustomToGraphDialog').show();
        }
    }]
});

Zenoss.BaseSequenceGrid = Ext.extend(Ext.grid.GridPanel, {
    constructor: function(config){
        Ext.applyIf(config, {
            enableDragDrop: Zenoss.Security.hasPermission('Manage DMD'),
            ddGroup: 'sequenceDDGroup'
        });
        Zenoss.BaseSequenceGrid.superclass.constructor.call(this, config);
    },
    onRender: function() {
        Zenoss.BaseSequenceGrid.superclass.onRender.apply(this, arguments);
        var grid, store;
        grid = this;
        store = this.getStore();
        this.dropZone = new Ext.dd.DropZone(this.view.scroller.dom, {
            ddGroup: 'sequenceDDGroup',
            onContainerOver: function(source, event, data) {
                return this.dropAllowed;
            },
            notifyDrop: function(source, event, data) {
                var sm, rows, cindex, i, rowData;
                sm = grid.getSelectionModel();
                rows = sm.getSelections();
                cindex = source.getDragData(event).rowIndex;
                if (typeof cindex != "undefined") {
                    for (i = 0; i < rows.length; i++) {
                        rowData = store.getById(rows[i].id);
                        store.remove(store.getById(rows[i].id));
                        store.insert(cindex, rowData);
                    }
                    sm.selectRecords(rows);
                }
            }
        });
    }
});

Zenoss.GraphPointGrid = Ext.extend(Zenoss.BaseSequenceGrid, {
    constructor: function(config){
        Ext.applyIf(config, {
            stripeRows: true,
            autoScroll: true,
            border: false,
            listeners: {
                /**
                 * The selection model was being ignored at this point so I used the
                 * row click.
                 **/
                click: function() {
                    var record = getSelectedGraphPoint();
                    if (record) {
                        Ext.getCmp('deleteGraphPointButton').enable();
                        Ext.getCmp('editGraphPointButton').enable();
                    }else{
                        Ext.getCmp('deleteGraphPointButton').disable();
                        Ext.getCmp('editGraphPointButton').disable();
                    }
                },
                rowdblclick: displayGraphPointForm
            },
            autoExpandColumn: 'description',
            store: {xtype: 'graphpointstore'},
            columns: [
                {dataIndex: 'name', header: _t('Name'), width: 150},
                {dataIndex: 'type', header: _t('Type'), width: 150},
                {dataIndex: 'description', header: _t('Description'), id: 'description'}
            ],
            tbar: [{
                xtype: 'button',
                id: 'addGraphPointButton',
                iconCls: 'add',
                tooltip: _t('Add Graph Point'),
                menu: 'graphPointMenu'
            }, {
                xtype: 'button',
                id: 'deleteGraphPointButton',
                iconCls: 'delete',
                disabled: true,
                tooltip: _t('Delete Graph Point'),
                handler: function() {
                    var html, dialog;
                    // format the confimation message
                    html = _t("Are you sure you want to remove the graph point, {0}?") + "<br />" +
                        _t("There is no undo.");
                    html = String.format(html, getSelectedGraphPoint().data.name);
                    
                    // show the dialog
                    dialog = Ext.getCmp('deleteGraphPointDialog');
                    dialog.show();
                    dialog.getComponent('message').update(html);                    
                }
            }, {
                xtype: 'button',
                id: 'editGraphPointButton',
                iconCls: 'customize',
                disabled: true,
                tooltip: _t('Edit Graph Point'),
                handler: displayGraphPointForm
            }]
        });
        Zenoss.GraphPointGrid.superclass.constructor.call(this, config);
    }
});
Ext.reg('graphpointgrid', Zenoss.GraphPointGrid);

/**********************************************************************
 *
 * Graph Point Edit Dialog/Grid
 *
 */

function reloadGraphPoints() {
    var grid = Ext.getCmp('graphPointGrid');
    grid.getStore().reload();
}

/**
 * Call back function from when a user selects a graph point.
 * This shows yet another dialog for editing a graph point
 **/
function displayGraphPointForm() {
    var record = getSelectedGraphPoint();

    function displayEditDialog(response) {
        var win = Ext.create( {
            record: response.data,
            items: response.form,
            singleColumn: true,
            width: 400,
            xtype: 'datasourceeditdialog',
            title: _t('Edit Graph Point'),
            directFn: router.setInfo,
            id: 'editGraphPointDialog',
            saveHandler: reloadGraphPoints
        });

        win.show();
    }

    // remote call to get the object details
    router.getInfo({uid: record.id}, displayEditDialog);
}

new Zenoss.HideFitDialog({
    id: 'manageGraphPointsDialog',
    title: _t('Manage Graph Points'),
    items: [{
        xtype: 'graphpointgrid',
        id: 'graphPointGrid',
        ref: 'graphGrid'
    }],
    buttons: [
    {
        xtype: 'HideDialogButton',
        text: _t('Save'),
        handler: function(){
            if (Zenoss.Security.hasPermission('Manage DMD')) {
                var records, uids;
                records = Ext.getCmp('graphPointGrid').getStore().getRange();
                uids = Ext.pluck(records, 'id');
                router.setGraphPointSequence({'uids': uids});
            }
        }
    }, {
        xtype: 'HideDialogButton',
        text: _t('Cancel')
    }]
});

Ext.create({
    xtype: 'window',
    id: 'viewGraphDefinitionDialog',
    title: _t('View and Edit Graph Definition'),
    closeAction: 'hide',
    buttonAlign: 'left',
    autoScroll: true,
    plain: true,
    modal: true,
    padding: 10,
    buttons: [{
        ref: '../submitButton',
        text: _t('Submit'),
        handler: function(submitButton){
            var dialogWindow, basicForm, params;
            dialogWindow = submitButton.refOwner;
            basicForm = dialogWindow.formPanel.getForm();
            params = Ext.applyIf(basicForm.getValues(), {
                uid: dialogWindow.uid
            });
            basicForm.api.submit(params, function() {
                                     Ext.getCmp('graphGrid').getStore().reload();
                                 });
            dialogWindow.hide();
        }
    },{
        ref: '../cancelButton',
        text: 'Cancel',
        handler: function(cancelButton){
            var dialogWindow = cancelButton.refOwner;
            dialogWindow.hide();
        }
    }],
    items: {
        xtype: 'form',
        ref: 'formPanel',
        labelAlign: 'top',
        monitorValid: true,
        border: false,
        paramsAsHash: true,
        api: {
            load: router.getGraphDefinition,
            submit: router.setGraphDefinition
        },
        listeners: {
            clientvalidation: function(formPanel, valid){
                var dialogWindow;
                dialogWindow = formPanel.refOwner;
                dialogWindow.submitButton.setDisabled( ! valid );
            },
            show: function(formPanel){
                formPanel.getForm().load();
            }
        },
        items: [{
            xtype: 'textfield',
            fieldLabel: _t('Name'),
            name: 'name',
            allowBlank: false
        },{
            xtype: 'numberfield',
            fieldLabel: _t('Height'),
            name: 'height',
            minValue: 0
        },{
            xtype: 'numberfield',
            fieldLabel: _t('Width'),
            name: 'width',
            minValue: 0
        },{
            xtype: 'textfield',
            fieldLabel: _t('Units'),
            name: 'units'
        },{
            xtype: 'checkbox',
            fieldLabel: _t('Logarithmic Scale'),
            name: 'log'
        },{
            xtype: 'checkbox',
            fieldLabel: _t('Base 1024'),
            name: 'base'
        },{
            xtype: 'numberfield',
            fieldLabel: _t('Min Y'),
            name: 'miny'
        },{
            xtype: 'numberfield',
            fieldLabel: _t('Max Y'),
            name: 'maxy'
        },{
            xtype: 'checkbox',
            fieldLabel: _t('Has Summary'),
            name: 'hasSummary'
        }]
    },
    loadAndShow: function(uid) {
        this.uid = uid;
        this.formPanel.getForm().load({
            params: {uid:uid},
            success: function() {
                this.show();
            },
            scope: this
        });
    }
});

new Ext.menu.Menu({
    id: 'graphDefinitionMenu',
    items: [{
        xtype: 'menuitem',
        text: _t('Manage Graph Points'),
        handler: function(){
            var uid, store;
            uid = getSelectedGraphDefinition().id;
            Ext.getCmp('manageGraphPointsDialog').show();
            store = Ext.getCmp('graphPointGrid').getStore();
            store.setBaseParam('uid', uid);
            store.load();
        }
    }, {
        xtype: 'menuitem',
        text: _t('View and Edit Details'),
        handler: function(){
            var dialogWindow, uid;
            dialogWindow = Ext.getCmp('viewGraphDefinitionDialog');
            uid = getSelectedGraphDefinition().id;
            dialogWindow.loadAndShow(uid);
        }
    },{
        xtype: 'menuitem',
        text: _t('Custom Graph Definition'),
        handler: function () {
            var win = Ext.getCmp('graphCustomDefinitionDialog'),
                uid = getSelectedGraphDefinition().id;
            win.loadAndShow(uid);
        }
    },{
        xtype: 'menuitem',
        text: _t('Graph Commands'),
        handler: function () {
            var params = {
                uid: getSelectedGraphDefinition().id
            };

            router.getGraphDefinition(params, function (response) {
                Ext.MessageBox.show({
                    title: _t('Graph Commands'),
                    minWidth: 700,
                    msg: String.format('<pre>{0}</pre>', response.data.fakeGraphCommands),
                    buttons: Ext.MessageBox.OK
                });
            });
        }
    }]
});

Zenoss.templates.GraphGrid = Ext.extend(Ext.grid.GridPanel, {
    constructor: function(config) {
        Ext.applyIf(config, {
            title: _t('Graph Definitions'),
            store: {xtype: 'graphstore'},
            listeners: {
                /**
                 * Double click to edit a graph definition
                 **/
                rowdblclick: function()  {
                    var dialogWindow, uid;
                    dialogWindow = Ext.getCmp('viewGraphDefinitionDialog');
                    uid = getSelectedGraphDefinition().id;
                    dialogWindow.loadAndShow(uid);
                }

            },
            selModel: new Ext.grid.RowSelectionModel({
                singleSelect: true,
                listeners: {
                    rowdeselect: function() {
                        Ext.getCmp('deleteGraphDefinitionButton').disable();
                        Ext.getCmp('graphDefinitionMenuButton').disable();
                    },
                    rowselect: function() {
                        Ext.getCmp('deleteGraphDefinitionButton').enable();
                        Ext.getCmp('graphDefinitionMenuButton').enable();
                    }
                }
            }),
            colModel: new Ext.grid.ColumnModel({
                columns: [
                    {dataIndex: 'name', header: _t('Name'), width: 400}
                ]
            }),
            tbar: [{
                id: 'addGraphDefinitionButton',
                xtype: 'button',
                iconCls: 'add',
                tooltip: _t('Add Graph Definition'),
                handler: function() {
                    Ext.getCmp('addGraphDefinitionDialog').show();
                }
            }, {
                id: 'deleteGraphDefinitionButton',
                xtype: 'button',
                iconCls: 'delete',
                tooltip: _t('Delete Graph Definition'),
                disabled: true,
                handler: function() {
                    var msg, name, html, dialog;
                    msg = _t("Are you sure you want to remove {0}? There is no undo.");
                    name = getSelectedGraphDefinition().data.name;
                    html = String.format(msg, name);
                    dialog = Ext.getCmp('deleteGraphDefinitionDialog');
                    dialog.show();
                    dialog.getComponent('message').update(html);
                }
            }, {
                id: 'graphDefinitionMenuButton',
                xtype: 'button',
                iconCls: 'customize',
                menu: 'graphDefinitionMenu',
                disabled: true
            }]
        });
        Zenoss.templates.GraphGrid.superclass.constructor.call(this, config);
    }
});
Ext.reg('graphgrid', Zenoss.templates.GraphGrid);

})();
