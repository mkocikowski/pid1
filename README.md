Why
---
This is about the Docker "PID1 zombie reaping problem":

- https://news.ycombinator.com/item?id=8916785
- https://blog.phusion.nl/2015/01/20/docker-and-the-pid-1-zombie-reaping-problem/
- http://blog.dscpl.com.au/2015/12/issues-with-running-as-pid-1-in-docker.html

tl;dr
---

- detect with `ps -ef | grep [d]efunct`
- if there is no problem, there is no problem
- if there is a problem, can you fix the code you are deploying?
- consider `docker run --pid=host` as remedy, but **only when problem present** (and see security considerations below)
- when everything else fails, opt for complexity

Reproduce
---
Build and run the container (everything that follows tested with docker 1.9.1 and 1.10.1):

```
docker build -t pid1 .
docker run -it --rm -v $(pwd)/orphanmaker.py:/opt/orphanmaker/orphanmaker.py pid1 /opt/orphanmaker/orphanmaker.py
```

This will block. In a separate terminal on docker host list python processes:

```
docker@default:~$ ps -ef | grep [y]thon
docker    1676  1263  0 18:32 pts/0    00:00:00 /usr/bin/python /opt/orphanmaker/orphanmaker.py
docker    1681  1676  0 18:32 pts/0    00:00:00 [python] <defunct>
docker    1682  1676  0 18:32 pts/0    00:00:00 [python] <defunct>
docker@default:~$ 
```

The first process is the 'parent', second is the 'child', third is the 'grandchild'. The child forked the grandchild and then quit (orphaning the grandchild); then the grandchild quit, and instead of being reaped, became a zombie (and this is the problem). Had the grandchild been reaped, we'd see only one defunct process (the child, which is dead, but whose parent is still alive). See bootnote for more info on this.

Prevent
---
Go back to the terminal where you launched the container, and kill it. Now do this:

```
docker run -it --rm -v $(pwd)/orphanmaker.py:/opt/orphanmaker/orphanmaker.py --pid=host pid1 /opt/orphanmaker/orphanmaker.py
...
docker@default:~$ ps -ef | grep [y]thon
docker    1746  1263  1 18:34 pts/0    00:00:00 /usr/bin/python /opt/orphanmaker/orphanmaker.py
docker    1751  1746  0 18:34 pts/0    00:00:00 [python] <defunct>
docker@default:~$ 
```

Thanks to the `--pid=host` argument, the grandchild is reaped correctly (by the host process #1).

Security implications
---
**A docker container running as root has full control of the host system.** Pid namespacing alleviates this, but still: you run a container as root, that container has full control of the host. Solution: don't run your container as root. This is basic sanity. Always specity 'USER' in the Dockerfile, or do `docker run --user=`. **When you run with `--pid=host` as root, then code inside your container can see - and kill - any process on the host.**

Bootnote
---
The `--pid` flag came in with [Docker 1.5 in Feb 2015](https://github.com/docker/docker/blob/master/CHANGELOG.md#150-2015-02-10). It makes the docker container share the pid 'namespace' with the host; this means that when the orphaned process in the container is assigned ppid 1, it is the host pid 1, not the container pid 1. The container pid 1 is the 'orphanmaker' (will not reap), but the host pid 1 is the host init process (which will reap). Going back to the not-reaped example:

```
docker@default:~$ ps -ef | grep [y]thon
docker    1676  1263  0 18:32 pts/0    00:00:00 /usr/bin/python /opt/orphanmaker/orphanmaker.py
docker    1681  1676  0 18:32 pts/0    00:00:00 [python] <defunct>
docker    1682  1676  0 18:32 pts/0    00:00:00 [python] <defunct>
docker@default:~$ 
```

The ppid of the grandchild is the pid of the parent. This is because on being orphaned, the grandchild was assigned ppid 1 inside the container. Pid 1 inside the container is the host pid 1676. 

Bootthoughts
---
 - reaping by pid 1 applies only to orphaned processes
 - if a process was forked, exited, and not wait()ed on by its parent, it will stick around for as long as the parent lives
 - this is a resource leak, ie a bug in application code
 - I'd rather deal with causes than with symptoms (cause: bad application code; symptom: zombies)


