$(function() {
    function OctoCamDoxSettingsViewModel(parameters) {
        var self = this;

        self.picture_folder_uploads = ko.observable(undefined);
    }


    // This is how our plugin registers itself with the application, by adding some configuration information to
    // the global variable ADDITIONAL_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push({
        // This is the constructor to call for instantiating the plugin
        construct: OctoCamDoxSettingsViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request here is the order
        // in which the dependencies will be injected into your view model upon instantiation via the parameters
        // argument
        dependencies: ["settingsViewModel", "controlViewModel", "connectionViewModel"],

        // Finally, this is the list of all elements we want this view model to be bound to.
        elements:["#settings_plugin_OctoCamDox"]
    });
});
