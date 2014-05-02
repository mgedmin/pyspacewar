How to make a PySpaceWar release
================================

(Because I forget)


1. Change the version number in src/pyspacewar/version.py
2. Update NEWS.txt
3. Commit.
4. Tag the release

     bzr tag $version

5. Build the tarball and zip file

     python setup.py sdist --formats=gztar,zip

6. Test the archives: go to a temporary directory, untar the tarball, run the
   game (./pyspacewar), run the unit tests (./test.py), make a sdist again
   and check that it is the same as the first one.

7. Upload the tarballs and update the pyspacewar website

     python setup.py sdist --formats=gztar,zip register upload
     mv dist/* ~/www/pyspacewar/
     cd ~/www/pyspacewar
     svn add *$version*
     vi index.html news.txt
       update the News and Download sections at the very least
     svn ci

8. Increase version number in src/pyspacewar/version.py, add 'dev' suffix,
   commit.

9. Push changes to Launchpad

     bzr push

10. Announce the new release on pygame.org, the pygame mailing list, my
    weblog.  Maybe.

    PyGame: log in at http://pygame.org/
    The list: pygame-users@seul.org

