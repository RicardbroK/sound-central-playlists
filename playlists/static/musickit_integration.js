StartImport = async function() {
    try {
        console.log("Fetching developer token...");
        const response = await fetch('/playlists/apple/generateToken', {
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest', // Necessary to work with request.is_ajax()
            },
        });
        const data = await response.json();
        const developerToken = data.apple_music_token;
        console.log("Developer Token received: ", developerToken);

        console.log("Configuring MusicKit...");
        await MusicKit.configure({
            developerToken: developerToken,
            app: {
                name: 'My Cool Web App',
                build: '1978.4.1',
            },
        });
        console.log("MusicKit configured successfully.");

        const music = MusicKit.getInstance();
        console.log("Attempting to authorize...");
        const musicUserToken = await music.authorize();
        console.log('Authorization attempt finished.');

        if (music.isAuthorized) {
            console.log('Authorization successful. Music User Token:', musicUserToken);
        } else {
            console.log('Authorization failed. No user token received.');
            return; // Stop further execution if not authorized
        }

        const playlistId = document.getElementById('playlist_id').textContent;
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        console.log("Playlist ID: ", playlistId);

        let playlist_info = await music.api.music(`/v1/catalog/us/playlists/${playlistId}`);
        let playlist_attributes = playlist_info.data.data[0];
        console.log('Playlist Attributes:', playlist_attributes);
        
        const pageSize = 25;
        const urlPath = `/v1/catalog/us/playlists/${playlistId}/tracks`;
        const tracks = [];
        let hasNextPage = true;
        while (hasNextPage) {
          const queryParameters = {
            limit: pageSize,
            offset: tracks.length,
          };
          const response = await music.api.music(urlPath, queryParameters);
          tracks.push(...response.data.data);
          hasNextPage = !!response.data.next;
        }
        console.log('Playlist Tracks:', tracks);

        $.ajax({
            url: '/playlists/apple/',
            type: 'POST',
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': csrfToken  // Set the CSRF token in the request headers
            },
            data: JSON.stringify({
                playlist_attributes: JSON.stringify(playlist_attributes),
                playlist_songs: JSON.stringify(tracks),
            }),
            success: function(response) {
                console.log('Data sent successfully', response);
                window.location.href  = ('/playlists/view/'+response['created_playlist'])
            },
            error: function(error) {
                console.error('Error sending data', error);
            }
        });
    } catch (err) {
        console.error('MusicKit configuration or processing error:', err);
        alert("Error during MusicKit initialization or operation. Please check the console for more details.");
    }
};