    function signInCallback(authResult) {
        if (authResult['code']) {
            $('#signinButton').attr('style', 'display:none');
            $.ajax({
                type: 'post',
                url: '/gconnect?state='+state,
                processData: false,
                contentType: 'application/octet-stream;charset=utf-8',
                data: authResult['code'],
                success: function(result) {
                    if (result) {
                        $('#result').html('Login successfully</br>' + result)
                        setTimeout(function() {
                            window.location.href = home_url;
                        }, 1000)
                    }
                }
            })
        }
        else if(authResult['error'])
            console.log('there was an error: ' + authResult['error']);
        else
            $('#result').html('failed to make server side call check your configuration and console')


    }