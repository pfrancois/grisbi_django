(function (window, $) {

  function autocompletion($input) {
    $input.autocomplete({minLength:3, source:'/xhr/users/'});
  }

  var
    utils = BB.utils,
    guard = utils.guard,
    join = utils.join,
    placeholder = utils.placeholder;

  // Date and time localization
  $.fn.localize(function () {
    var d, h, int = function (n) { return n >> 0; }, m, names, pad, s, units;

    pad = function (num) { return (num + 100 + '').substr(1); };

    // This code looks a little odd because it resembles as closely
    // as possible the Python function `pretty_timedelta` defined in
    // apps/bb/helpers.py. The same logic must be used in both places
    // since the Python code determines the initial values while the
    // JavaScript code updates these values every minute. Having the
    // functions return the same value for a given input is desirable.

    // If you update this, update the corresponding Python code too!

    s = 1
    m = 60 * s
    h = 60 * m
    d = 24 * h
    units = [s, m, h, d]
    names = 'second minute hour day'.split(' ')

    return function (date, countdown) {
        var delta, i, n, suffix;

        delta = int((date - new Date) / 1000) || -1

        if (delta < 0) {
            delta = -delta
            if (delta < 10)
                return 'just now'
            suffix = 'ago'
        } else {
            suffix = 'left'
            if (!countdown) {
                if (delta < 300) // ignore discrepancies of up to five minutes
                    return 'just now'
                suffix = 'from now'
            }
        }

        // Use yyyy-mm-dd format for events older than 30 days.
        if (delta > 30 * d)
            return [date.getFullYear(), pad(date.getMonth() + 1), pad(date.getDate())].join('-')

        i = units.length

        while (i) {
            i -= 1
            if (i === 0 || delta > units[i]) {
                n = int(delta / units[i])
                return [n, n === 1? names[i]: names[i] + 's', suffix].join(' ')
            }
        }
    };
  }());

  (function () {
    // relativize dates and times
    (BB.localize = function () {
      $('time').each(function () {
        var $this = $(this), $time;
        var siteMessageElem = $('.site-message')[0];
        if (siteMessageElem && $.contains(siteMessageElem, this)) {
          $this.localize({
            format: 'h:MMa, d mmmm yyyy (UTCZ)',
            periods: ['am', 'pm']
          });
        }
        else if ($this.data('format')) {
          $this.localize({
            format: $this.data('format'),
            periods: $this.data('associated-press-periods') ? ['a.m.', 'p.m.'] : void 0
          });
        }
        // ignore elements with data-relative="false"
        else if ($this.data('relative') !== false) {
          $this.localize(null, $this.data('countdown')); // curry `countdown`
        }
        if ($this.data('title')) {
          // IE8 doesn't allow `time` elements to be cloned. :\
          $time = $(document.createElement('time'));
          _.each(
            this.attributes,
            function (attr) {
              $time.attr(attr.name, attr.value);
            }
          );
          $this.attr('title', $time.localize('d mmmm yyyy HH:MM').text());
        }
      });
    })();
    // repeat every 60 seconds
    window.setInterval(BB.localize, 6e4);
  }());

  // `autofocus` support for outdated browsers (Modernizr?)
  if (!('autofocus' in document.createElement('input'))) {
    guard('input[autofocus]', function ($el) { $el.focus(); });
  }

  // `placeholder` support for outdated browsers
  placeholder();

  // Follow buttons
  $('a.follow').click(function (event) {
    event.preventDefault();
    var
      $this = $(this),
      $followersCount = $('#followers-count'),
      className = $this.attr('class'),
      text = $this.text(),
      url = $this.attr('href');

    if ($this.hasClass('loading')) return;

    $this
      .addClass('loading')
      .removeClass('following')
      .text('updating');

    $.get(
      url,
      function (data) {
        var
          following = data.following,
          type = data.type;
        // anonymous user
        if (following === void 0) {
          // restore state before redirecting (don't break the "back" button)
          $this.attr('class', className).text(text);
          return (window.location.pathname = url);
        }
        // authenticated user
        $followersCount.text(data.followers);
        if (following) {
          $this.addClass('following').text('following').removeClass('loading');
          $this.parent().addClass('following');

          // register Google Analytics follow events
          if (type === 'repo') {
            BB.gaqPush(
              ['atl._trackPageview', '/repo/follow'],
              ['atl._trackEvent', 'Share', 'Follow Repo']
            );
          } else if (type === 'user') {
            BB.gaqPush(
              ['atl._trackPageview', '/user/follow'],
              ['atl._trackEvent', 'Share', 'Follow User']
            );
          }
        } else {
          $this
            .removeClass('following')
            .text('follow')
            .removeClass('loading')
            .parent()
              .removeClass('following');
        }
      }
    );
  });

  // Private users
  guard('#private-users', function ($privateUsers) {
    var
      $errorList = $('<ul class="errorlist"></ul>').appendTo('#add-private-user'),
      $numUsers = $('#num-users'),
      $username = $('#username').focus(),
      maxUsers = +$('#max-users').text(),
      numUsers = +$numUsers.text(),
      overLimit = numUsers > maxUsers,
      queue = [];

    function updateCount(n) {
      // situation has been rectified
      if (overLimit && n <= maxUsers) {
        // fadeTo is used because fade sets "display:none" upon completion
        var $message = $('#plans-and-billing .warning.message');
        $message.fadeTo('fast', 0, function () { $message.slideUp(); });
        $('#too-many-users').remove();
      }
      overLimit = (numUsers = n) > maxUsers;
      return $numUsers.text(n);
    }

    // reveal/conceal a list of private repos to which a user has access
    $privateUsers.delegate('li[data-username] b', 'click', function () {
      var $user = $(this).parent();

      if ($user.hasClass('loading')) return;
      if ($user.hasClass('revealed') || $user.data('retrieved')) return $user.bb('toggle');

      $user.addClass('loading');

      $.post(
        'repos/private',
        {username: $user.attr('data-username')},
        function (data, status) {
          if (status !== 'success') return;
          var repos = [];
          _.each(
            data,
            function (repo) {
              var access = repo.access;
              repos.push([
                '<li data-slug="', repo.slug, '"><a href="', repo.url, '">', repo.name, '</a><ul class="access"><li',
                access === 'read' ? ' class="selected"' : '', '>read</li><li',
                access === 'write' ? ' class="selected"' : '', '>write</li><li',
                access === 'admin' ? ' class="selected"' : '', '>admin</li></ul><a href="#delete">Delete</a></li>'
              ].join(''));
            }
          );
          $user
            .data('retrieved', true)
            .append('<ol class="children" style="display:none">' + repos.join('') + '</ol>')
            .bb('reveal');
        }
      );
    });

    // revoke a user's access to all private repos
    $privateUsers.delegate('li[data-username]>a[href="#delete"]', 'click', function (event) {
      event.preventDefault();
      var $user = $(this).addClass('loading').parent();
      $.post(
        'repos/private/user/remove',
        {username: $user.attr('data-username')},
        function (data, status) {
          updateCount(data.users);
          $user.bb('remove');
        }
      );
    });

    // revoke a user's access to a single private repo
    $privateUsers.delegate('li[data-slug]>a[href="#delete"]', 'click', function (event) {
      event.preventDefault();
      var $repo = $(this).addClass('loading').parent();
      $.post(
        'repos/private/repo/user/update',
        {username: $repo.closest('li[data-username]').attr('data-username'), slug: $repo.attr('data-slug')},
        function (data, status) {
          updateCount(data.users);
          $repo.bb('remove');
        }
      );
    });

    // change a user's access level for a single private repo
    $privateUsers.delegate('.access>li', 'click', function (event) {
      var $this = $(this), $deleteButton, data;
      if ($this.hasClass('selected')) return;
      $deleteButton = (
        $this
          .closest('li[data-slug]')
          .find('a[href="#delete"]')
          .addClass('loading')
      );
      data = {
        username: $this.closest('li[data-username]').attr('data-username'),
        slug: $this.closest('li[data-slug]').attr('data-slug'),
        level: {
          read: 'readers',
          write: 'writers',
          admin: 'admins'
        }[$this.text()]
      };
      $.post(
        'repos/private/repo/user/update',
        data,
        function (data) {
          $deleteButton.removeClass('loading');
          $this.bb('select');
        }
      );
    });

    // grant a user access to all private repos
    $('#add-private-user')
      .find('input[type="submit"]')
        .click(function (event) {
          event.preventDefault();
          $.ajax({
            url: 'repos/private/user/add',
            type: 'POST',
            data: {
              give_access: 1,
              username: $username.val(),
              level: $('#id_level').val()
            },
            error: function (xhr) {
              var $error, id;
              while (id = queue.shift()) window.clearTimeout(id);
              $error = (
                $('<li>' + xhr.responseText + '</li>')
                  .css({position: 'absolute', left: -9999})
                  .appendTo($errorList)
              );
              $errorList
                .animate(
                  {height: $errorList.innerHeight() + $error.outerHeight()},
                  function () {
                    $error
                      .css({position: 'relative', left: 'auto', opacity: 0})
                      .animate({opacity: 1});
                    queue.push(BB.delay(3000, function () {
                      var $children = $errorList.children();
                      $children.fadeOut(function () {
                        $errorList.animate({height: 0}, function () {
                          $children.remove();
                        });
                      });
                    }));
                  }
                );
            },
            success: function (data) {
              // register Google Analytics share events
              BB.gaqPush(
                ['atl._trackPageview', '/repo/share'],
                ['atl._trackEvent', 'Share', 'Share Repo']
              );
              updateCount(data.users);
              $privateUsers.bb('insert', data);
              $username.val('').focus();
            }
          });
        });
        autocompletion($username);
  });

  // Username mappings
  guard('#username-mappings', function ($usernameMappings) {
    var
      $committer = $('#committer'),
      $username = $('#username'),
      $message = $('<p></p>'),
      $error = $('<div class="error message"></div>').hide().append($message).prependTo('#username-mappings-div'),
      pathname = window.location.pathname.replace(/^(.*?)\/*$/, '$1'),
      error = (function () {
        function slide() {
          timeoutId = null;
          $error.animate({opacity: 0}, function () {
            $error.slideUp();
          });
        }
        var timeoutId;
        return function (xhr) {
          var height, message = $.parseJSON(xhr.responseText).msg;
          if (timeoutId) {
            window.clearTimeout(timeoutId);
            // replace current error message
            $message.fadeOut('slow', function () {
              $message.text(message).fadeIn('slow');
            });
            return (timeoutId = BB.delay(5000, slide));
          }
          // full animation
          $error.css({position: 'absolute', left: -9999});
          $message.text(message);
          height = $error.height();
          $error
            .css({position: 'relative', left: 'auto', height: 0, opacity: 0})
            .show()
            .animate(
              {height: height},
              function () {
                $error
                  .css('height', 'auto')
                  .animate({opacity: 1});
              }
            );
          return (timeoutId = BB.delay(5000, slide));
        };
      }());

    // add a (repo, user, alias) tuple
    $('#add-username-mapping').find('input[type="submit"]').click(function (event) {
      event.preventDefault();
      $.ajax({
        url: [pathname, $username.val().trim(), $committer.val().trim()].join('/'),
        type: 'PUT',
        error: error,
        success: function (data, status) {
          var
            username = data.username,
            $user = $usernameMappings.find('li[data-username="' + username + '"]');
          data.text = data.committer;
          ($user.length ? $user.find('.children') : $usernameMappings).bb('insert', data, true);
          $committer.val('');
        }
      });
    });

    // delete a (repo, user, alias) tuple
    $('#username-mappings').delegate('ol a[href="#delete"]', 'click', function (event) {
      event.preventDefault();
      var $this = $(this);
      $.ajax({
        url: [pathname, $this.closest('li[data-username]').data('username'), $this.prev().text()].join('/'),
        type: 'DELETE',
        error: error,
        success: function () { $this.parent().bb('remove'); }
      });
    });

    // delete all (repo, user, alias) tuples which match this repo and the specified user
    $('#username-mappings').delegate('li[data-username]>a[href="#delete"]', 'click', function (event) {
      event.preventDefault();
      var $this = $(this);
      $.ajax({
        url: pathname + '/' + $this.closest('li[data-username]').data('username'),
        type: 'DELETE',
        error: error,
        success: function () { $this.parent().bb('remove'); }
      });
    });

    // toggle
    $('#username-mappings').delegate('li[data-username] b', 'click', function () {
      $(this).parent().bb('toggle');
    });

    autocompletion($username);
  });

  // OpenID
  guard('#sign-in,#signup,#associate-openid', function ($signin) {
    var
      $openId = $signin.find('.opensocial'),
      $openIdLink = $('.show-open-id>a'),
      $openIdSubmit = $openId.find('#openid_submit'),
      $selectedButton = $(),
      $selectedInput = $(),
      $standard = $signin.find('.standard'),
      $standardLink = $('.show-standard-signin>a'),
      cookieOptions = {expires: 365},
      openIdProviderHash = $.cookie('openid-provider');

    function select(button, input) {
      $selectedButton.add($selectedInput).removeClass('selected');
      $selectedButton = $(button).addClass('selected');
      $selectedInput = $(input).addClass('selected');
      $selectedInput.find('input').focus();
      $openIdSubmit.show();
      $.cookie('openid-provider', $selectedButton.attr('href'), cookieOptions);
    }

    if ($.cookie('login-method') === 'openid' || /\/openids\//.test(window.location.href)) {
      $standard.hide();
      $openIdLink.parent().hide();
      $openId.show();
      $standardLink.parent().show();
      if (openIdProviderHash) {
        select('a[href="' + openIdProviderHash + '"]', openIdProviderHash);
      }
    }

    $openIdLink.click(function (event) {
      event.preventDefault();
      $standard.fadeOut('fast', function () {
        $openId.fadeIn('fast', function () {
          var openIdProviderHash = $.cookie('openid-provider');
          select('a[href="' + openIdProviderHash + '"]', openIdProviderHash);
        });
      });
      $openIdLink.parent().hide();
      $standardLink.parent().show();
      $.cookie('login-method', 'openid', cookieOptions);
    });

    $standardLink.click(function (event) {
      event.preventDefault();
      $openId.fadeOut('fast', function () { $standard.fadeIn('fast'); });
      $standardLink.parent().hide();
      $openIdLink.parent().show();
      $.cookie('login-method', 'standard', cookieOptions);
    });

    $openId.find('.badges a').click(function (event) {
      var $this = $(this), href = $this.attr('href');
      if ($this.data('url')) {
        select(this, href);
      } else {
        $.cookie('openid-provider', href, cookieOptions);
        window.location.assign(href);
      }
      event.preventDefault();
    });

    $openIdSubmit.click(function () {
      var id = $selectedInput.find('input').val();
      $('#openid_provider').val($selectedButton.data('url').replace('{id}', id));
      $('#openid_username').val(id);
      $('#openid_form').submit();
    });
  });

  // Fork at...
  $('#fp_sel').change(function () {
    if (this.value === 'specific') {
      $('#fp_specific').css('visibility', 'visible');
      $('#fp_specific_input').focus();
    } else {
      $('#fp_specific').css('visibility', 'hidden');
      $('#fp_specific_input').val(this.value);
    }
  });

  $('#repositories,#relevant-repos,#descendants,#trending-repositories,#featured-repositories').delegate('.followers .info-button-action a', 'click', utils.enableFollowingLinks );

  // select/deselect all messages
  $('#notification-controls').find(':checkbox').click(function () {
    var checked = this.checked;
    $('#notifications').find(':checkbox').each(function () { this.checked = checked; });
  });

  // Wiki new page form
  guard('#wiki-nav-links', function ($wikiNavLinks) {
    var $form = $('#wiki-new-page-form');

    $wikiNavLinks.find('.new').show().find('a').click(function (event) {
      event.preventDefault();
      $form.toggle();
    });

    $form.find('input[type="submit"]').click(function (event) {
      event.preventDefault();
      var page = $('#wiki-new-page').val().replace(/^\/+|\/+$/g, '');
      if (page.length) window.location = window.location.pathname.replace(/wiki\/(.*)$/, 'wiki/edit/' + page);
    });
  });

  $('#invitation-dialog').each(function () {
    var
      $invitation = $(this),
      $form = $invitation.find('form'),
      $email = $form.find('input[name="email-address"]'),
      $trigger = $('#repo-menu .share, #repo-menu-links-mini .share, #invitation-blurb .share'),
      invitationsEndpoint = BB.api.endpoint('invitations', BB.repo.owner.username, BB.repo.slug);

    $trigger.click(function (event) {
      $invitation.dialog('open');
      event.preventDefault();
    });

    $invitation.dialog({
      // Options.
      autoOpen: false,
      buttons: {
        'Send invitation': function (event) {
          var $button = $(event.target);
          $form.trigger('submit', [$button]);
        }
      },
      modal: true,
      position: ['50%', 100],
      title: $invitation.attr('title'),
      width: 480,

      // Events.
      open: function () {
        $form.find('.success_.message_').hide();
        $form.find('.error_.message_').hide();
        $email.val('');
      }
    });

    $form.submit(function (event, $submit) {
      var
        $form = $(this),
        email = $email.val();

      $submit = $submit || $form.closest('.ui-dialog').children('.ui-dialog-buttonpane').find('button');

      event.preventDefault();

      if ($submit.attr('disabled')) return;

      var messages = {
        200: email + ' has been invited.',
        400: 'Please enter a valid email address.',
        401: 'You are not authorized to send invitations for this repository.',
        404: 'This repository no longer exists.',
        409: email + ' has already been invited.',
        500: 'There was a problem processing your request (500 Internal Server Error).'
      };

      $submit.attr('disabled', 'disabled');
      var
        buttonText = $submit.text(),
        buttonWidth = $submit.outerWidth(),
        buttonTimeout = BB.delay(200, function () {
          $submit
            .addClass('disabled')
            .width(buttonWidth)
            .text('Sending...');
        });

      $.ajax({
        type: $form.attr('method'),
        url: invitationsEndpoint.url(email),
        data: $form.serialize(),
        complete: function (xhr, status) {
          var
            $success = $form.find('.success_.message_').hide(),
            $error = $form.find('.error_.message_').hide();

          if (status === 'timeout') {
            $error
              .show()
              .find('h4').text('There was a problem connecting to the server.');
          } else if (messages.hasOwnProperty(xhr.status)) {
            var $message = xhr.status === 200 ? $success : $error;
            $message
              .show()
              .find('h4').text(messages[xhr.status]);
          }
          clearTimeout(buttonTimeout);
          $submit
            .removeAttr('disabled')
            .removeClass('disabled')
            .width('')
            .text(buttonText);
        },
        success: function (data, status, xhr) {
          if (xhr.status === 200) {
            // Make multiple email entry quicker by auto selecting the text.
            $email.select();
            BB.delay(1500, function () {
              // Auto close if not sending another invite.
              if (email === $email.val()) {
                $invitation.dialog('close');
              }
            });
            // Google Analytics.
            BB.gaqPush(['atl._trackEvent', 'Share', 'Invite user']);
          }
        }
      });
    });
  });

  $('#invitation-show-login').click(function (event) {
    event.preventDefault();
    $('#invitation-login')
      .show()
      .find('input:visible:first').focus();
  });

  guard('#invitation-accepted', function () {
    // Google Analytics.
    BB.gaqPush(['atl._trackEvent', 'Share', 'Invitation Accepted']);
  });

  $('#toggle-email-notifications').find('#id_email_notifications').click(function () {
    var $this = $(this), url = $this.parent('form').attr('action'), $label = $this.next('label');

    $this.css('visibility', 'hidden');
    $label.addClass('loading');

    $.get(url, function (data) {
      var toggle = data.toggle;
      $this.attr('checked', toggle);
      $this.css('visibility', 'inherit');
      $label.removeClass('loading');
    });
  });

  (function () {
    function enableAjaxFollow($repos) {
      var repoIds = BB.user.follows && BB.user.follows.repos;
      if (repoIds === void 0) return;

      $repos.find('.followers').addClass('followers-not-following');
      $repos.find('.info-button').removeClass('info-button-readonly');

      $(
        _.map(repoIds, function (id) { return '#id_repo_' + id; }).join()
      ).removeClass('followers-not-following').addClass('followers-following');
    }
    guard('#repositories', enableAjaxFollow);
    guard('#trending-repositories', enableAjaxFollow);
    guard('#featured-repositories', enableAjaxFollow);
    guard('#descendants', enableAjaxFollow);
  }());

  // Very ugly hack to suppress multiple email confirm messages (BB-1026).
  guard('#pending-address', function ($pendingAddressMessage) {
    if ($('#header-messages').find('.confirmation-successful').length) {
      $pendingAddressMessage.hide();
    }
  });

  $('a.revoke').click(function (event) {
    if (!confirm('Are you sure you want to revoke your access to this repository?')) {
      event.preventDefault();
    }
  });

  (function ($) { // "private" checkbox disabling
    function fn(event) {
      event.target.checked?
        this.removeAttr('disabled'):
        this.attr('disabled', 'disabled');
    }
    $('#id_has_wiki').change(fn.bind($('#id_wiki_private'))).change();
    $('#id_has_issues').change(fn.bind($('#id_issues_private'))).change();
  }($));

  // styling hook for "lingering" hover effects
  (function () {
    var
      className = 'hovering',
      $dropdowns =
        $('.inertial-hover')
          .each(function () {
            var
              $this = $(this),
              timeoutId = null;
            $this.mouseenter(function () {
              // Preclude multiple drop-downs
              // from being visible at once.
              $dropdowns.removeClass(className);
              if (timeoutId !== null) {
                window.clearTimeout(timeoutId);
                timeoutId = null;
              }
              $this.addClass(className);
            });
            $this.mouseleave(function () {
              timeoutId = BB.delay(500, function () {
                if (timeoutId !== null) {
                  $this.removeClass(className);
                }
              });
            });
          });
  }());

  // HTTPS/SSH toggle
  guard('#repo-desc-cloneinfo', function ($el) {
    var
      el = $el[0], https = 'https', ssh = 'ssh',
      addHandler = function (protocol) {
        $el
          .find('a.' + protocol)
            .click(
              function (event) {
                el.className = protocol;
                event.preventDefault();
              }
            );
      };

    el.className = BB.user.isSshEnabled? ssh: https;
    addHandler(https);
    addHandler(ssh);
  });

  $('#embed-link')
    .click(
      function (event) {
        var
          $this = $(this),
          $label = $('<label for="embedded-link">embed code:</label>'),
          $input = $('<input type="text" id="embedded-link" />');

        $input.val('<script src="' + $this.attr('href') + '"></script>');
        $input.replaceAll($this).before($label).select();
        event.preventDefault();
      }
    );

  // JSUDiff
  jQuery(function ($) {
    $('.jsudiff')
      .udiff(
        function (line, key) {
          var
            id, name,
            num = line.number[key];

          if (num) {
            name = line.file.name;
            id = (
              key === 'now' ?
                join('chg_', name.now, '_newline', num):
                join('chg_', name.then, '_oldline', num)
            );
            this
              .attr('id', id)
              .html(join('<a href="#', id, '">', num, '</a>'));
          }
        }
      );
  });

  $('#toggle-preview')
    .click(
      function (event) {
        $('#preview').toggle();
        event.preventDefault();
      }
    );

}(this, jQuery));
