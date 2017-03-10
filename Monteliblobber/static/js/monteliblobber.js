/**
 * Created by Andrew on 9/8/2016.
 */


var blobSubmitter = (function () {
    var blob_field = $('#id_blob');
    var blob_form_section = $('#blob_form');
    var loader = $('#loader');
    var header = $('#header_row');
    var resultsContainer = $('#results_editor');
    var instructionsContainer = $('#instructions_row');
    var resultsBlock = $('#results');

    var submitBlob = function () {

        var form = new FormData();
        loader.addClass("loader");
        form.append("blob", blob_field.val());
        resultsBlock.removeClass('hidden');
        sendAjax('/', 'POST', form, SubmissionCallback);

    };

    var ResultsCallback = function (resp) {
        resultsContainer.html(resp);
    };

    var SubmissionCallback = function (resp) {
        loader.removeClass("loader");
        blob_field.val('');
        header.addClass("hidden");
        blob_form_section.toggleClass("hidden");
        instructionsContainer.toggleClass("hidden");
        renderDataTable(resp);
    };

    var sendAjax = function (url, method, data, callback) {
        $.ajax({
            type: method,
            url: url,
            data: data,
            processData: false,
            contentType: false,

            success: function (response) {
                callback(response);
            },

            error: function (response) {
                console.log("error", response);
                $('#form_errors').html(response.responseText);
            }
        });
    };

    var renderDataTable = function (response) {
        var tab = $('#result_table').DataTable({
            dom: '<"row" <"col-sm-6" B><"col-sm-3" i><"col-sm-3" f>><"row" <"col-sm-12" rt>><"row" <"col-sm-2" l><"col-sm-10" p><"clear">>',
            data: response.data,
            columns: [
                {
                    title: "Value",
                    data: "value"
                },
                {
                    title: "Data Type",
                    data: "data_type"
                },
                {
                    title: "Tags",
                    data: "tags",
                    render: function (data, type, row) {
                        if (type === 'export') {
                            return data;
                        } else {
                            var tags = [];
                            for (i in data) {
                                tags.push('<span class="label label-default">' + data[i] + '</span>')
                            }
                            return tags;
                        }
                    }
                }
            ],
            lengthChange: true,
            select: true,
            buttons: [
                {
                    text: 'Select All',
                    action: function () {
                        tab.rows().select();
                    }
                },
                {
                    text: 'Select Inverse',
                    action: function () {
                        var selected = tab.rows({selected: true});
                        var notSelected = tab.rows({selected: false});
                        selected.deselect();
                        notSelected.select();
                    }
                },
                {
                    text: 'Select None',
                    action: function () {
                        tab.rows().deselect();
                    }
                },
                {
                    text: 'Delete Selected',
                    action: function () {
                        tab.rows({selected: true}).remove().draw();
                    }
                },
                {
                    extend: 'csvHtml5',
                    exportOptions: {orthogonal: 'export'}
                },
                {
                    extend: 'copyHtml5',
                    exportOptions: {orthogonal: 'export'}
                }
            ]
        });
    };

    var getResults = function () {
        resultsBlock.removeClass('hidden');
        $.getJSON('/results', null, function ( response ) {
            renderDataTable(response);
        });
    };

    return {
        submitBlob: submitBlob,
        getResults: getResults
    };


})();


var resourceController = (function () {
    var loader = $('#loader');

    var triggerUpdate = function (targetUrl, message) {
        loader.addClass("loader");
        $.ajax({
            type: 'POST',
            url: targetUrl,
            processData: false,
            contentType: false,

            success: function (response) {
                loader.removeClass("loader");
                $('#messages').append(response);
            },

            error: function (response) {
                loader.removeClass("loader");
                console.log("error", response);
                $('#form_errors').html(response.responseText);
            }
        });
    };

    var shutdownApplication = function () {
        loader.addClass("loader");
        $.ajax({
            type: 'POST',
            url: '/quit',
            processData: false,
            contentType: false,

            success: function (response) {
                loader.removeClass("loader");
                $('#messages').append(response);
            },

            error: function (response) {
                loader.removeClass("loader");
                console.log("error", response);
                $('#form_errors').html(response.responseText);
            }
        });
    };

    var sendUpdate = function (targetUrl, message) {
        triggerUpdate(targetUrl, message);
    };
    return {
        sendUpdate: sendUpdate,
        shutdownApplication: shutdownApplication
    };
})();
