document.addEventListener('musickitloaded', async function () {
    console.log("MusicKit loaded event triggered.");
    try {
        const developerToken = document.getElementById('apple_music_token').textContent;
        const playlistId = document.getElementById('apple_music_playlist_id').textContent;
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        //console.log("Developer Token: ", developerToken);
        console.log("Playlist ID: ", playlistId);

        await MusicKit.configure({
            developerToken: developerToken,
            app: {
                name: 'My Cool Web App',
                build: '1978.4.1',
            },
        });

        const music = MusicKit.getInstance();
        const musicUserToken = await music.authorize(); // This line attempts to authorize the user.

        // Log the music user token if authorization is successful
        if (musicUserToken) {
            console.log('Authorization successful. Music User Token:', musicUserToken);
        } else {
            console.log('Authorization failed. No user token received.');
        }
        let playlist_info = await music.api.music(`/v1/catalog/us/playlists/${playlistId}`);
        playlist_attributes = playlist_info.data.data[0];
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
        console.log(tracks);

        $.ajax({
            url: '/playlists/apple/',
            type: 'POST',
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': csrfToken  // Set the CSRF token in the request headers
            },
            data: JSON.stringify({
                playlist_attributes: JSON.stringify(playlist_attributes),
                playlist_songs: JSON.stringify(tracks)
            }),
            success: function(response) {
                console.log('Data sent successfully', response);
            },
            error: function(error) {
                console.log('Error sending data', error);
            }
        });
    } catch (err) {
        console.error('MusicKit configuration or processing error:', err);
    }
});
