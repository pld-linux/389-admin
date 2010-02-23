# TODO
# - merge with fedora-ds-admin.spec

#%global selinux_variants mls targeted

%define		subver	.a1
%define		rel		0.1
Summary:	389 Administration Server (admin)
Name:		389-admin
Version:	1.1.11
Release:	0%{?subver}.%{rel}
License:	GPL v2 and ASL 2.0
Group:		Daemons
URL:		http://directory.fedoraproject.org/
Source0:	http://directory.fedoraproject.org/sources/%{name}-%{version}%{subver}.tar.bz2
# Source0-md5:	2d5c5e2058429086bbced744590aba7f
#Patch1:	f11-httpd.patch
BuildRequires:	389-adminutil-devel
BuildRequires:	apache-devel
BuildRequires:	apr-devel
BuildRequires:	apr-util-devel
BuildRequires:	cyrus-sasl-devel
BuildRequires:	icu
BuildRequires:	libicu-devel >= 4.2.1
BuildRequires:	mozldap-devel
BuildRequires:	nspr-devel
BuildRequires:	nss-devel
BuildRequires:	svrcore-devel
%if %{with selinux}
# The following are needed to build the SELinux policy
BuildRequires:	/usr/share/selinux/devel/Makefile
BuildRequires:	389-ds-base-selinux-devel
BuildRequires:	checkpolicy
BuildRequires:	selinux-policy-devel
%endif
Requires:	389-ds-base
Requires:	apache-mod_nss
# the following are needed for some of our scripts
Requires:	nss-tools
Requires:	perl-Mozilla-LDAP
# for the init script
Requires(post,preun):	/sbin/chkconfig
Requires:	rc-scripts
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
389 Administration Server is an HTTP agent that provides management
features for 389 Directory Server. It provides some management web
apps that can be used through a web browser. It provides the
authentication, access control, and CGI utilities used by the console.

%package selinux
Summary:	SELinux policy for 389 Administration Server
Group:		Daemons
Requires:	%{name} = %{version}-%{release}
Requires:	389-ds-base-selinux
Requires:	selinux-policy

%description selinux
SELinux policy for the 389 Adminstration Server package.

%prep
%setup -q -n %{name}-%{version}%{subver}
#%patch1

%build
%{__aclocal} -I m4
%{__automake}
%{__autoconf}
export CFLAGS="%{rpmcflags} $(apu-1-config --includes)"
%configure \
	--disable-rpath \
	%{?with_selinux:--with-selinux}

%ifarch x86_64 ppc64 ia64 s390x sparc64
export USE_64=1
%endif

%{__make}

%if %{with selinux}
# Build the SELinux policy module for each variant
cd selinux-built
cp %{_datadir}/dirsrv-selinux/dirsrv.if .
cp %{_datadir}/dirsrv-selinux/dirsrv.te .
for selinuxvariant in %{selinux_variants}; do
	%{__make} NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile
	mv dirsrv-admin.pp dirsrv-admin.pp.${selinuxvariant}
	%{__make} NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile clean
done
cd -
%endif

%install
rm -rf $RPM_BUILD_ROOT

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

# make console jars directory
install -d $RPM_BUILD_ROOT%{_datadir}/dirsrv/html/java

# remove libtool and static libs
rm -f $RPM_BUILD_ROOT%{_libdir}/*.a
rm -f $RPM_BUILD_ROOT%{_libdir}/*.so
rm -f $RPM_BUILD_ROOT%{_libdir}/*.la
rm -f $RPM_BUILD_ROOT%{_libdir}/dirsrv/modules/*.a
rm -f $RPM_BUILD_ROOT%{_libdir}/dirsrv/modules/*.la

%if %{with selinux}
# Install the SELinux policy
cd selinux-built
for selinuxvariant in %{selinux_variants}; do
	install -d $RPM_BUILD_ROOT%{_datadir}/selinux/${selinuxvariant}
	install -p -m 644 dirsrv-admin.pp.${selinuxvariant} \
		$RPM_BUILD_ROOT%{_datadir}/selinux/${selinuxvariant}/dirsrv-admin.pp
done
cd -
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/chkconfig --add dirsrv-admin
/sbin/ldconfig

%preun
if [ "$1" = 0 ]; then
	%service dirsrv-admin stop
	/sbin/chkconfig --del dirsrv-admin
fi

%postun -p /sbin/ldconfig

%if %{with selinux}
%post selinux
if [ "$1" -le "1" ]; then # First install
	for selinuxvariant in %{selinux_variants}; do
		semodule -s ${selinuxvariant} -i %{_datadir}/selinux/${selinuxvariant}/dirsrv-admin.pp 2>/dev/null || :
	done
	fixfiles -R %{name} restore || :
	%service dirsrv-admin condrestart
fi

%preun selinux
if [ "$1" -lt "1" ]; then # Final removal
	for selinuxvariant in %{selinux_variants}; do
		semodule -s ${selinuxvariant} -r dirsrv-admin 2>/dev/null || :
	done
	fixfiles -R %{name} restore || :
	%service dirsrv-admin condrestart
fi

%postun selinux
if [ "$1" -ge "1" ]; then # Upgrade
	for selinuxvariant in %{selinux_variants}; do
		semodule -s ${selinuxvariant} -i %{_datadir}/selinux/${selinuxvariant}/dirsrv-admin.pp 2>/dev/null || :
	done
fi
%endif

%files
%defattr(644,root,root,755)
%doc LICENSE
%dir %{_sysconfdir}/dirsrv/admin-serv
%config(noreplace)%{_sysconfdir}/dirsrv/admin-serv/*.conf
%{_datadir}/dirsrv
%attr(754,root,root) /etc/rc.d/init.d/dirsrv-admin
%config(noreplace)%verify(not md5 mtime size) /etc/sysconfig/dirsrv-admin
%attr(755,root,root) %{_sbindir}/*
%attr(755,root,root) %{_libdir}/*.so.*
%{_libdir}/dirsrv
%{_mandir}/man8/*

%if %{with selinux}
%files selinux
%defattr(644,root,root,755)
%{_datadir}/selinux/*/dirsrv-admin.pp
%endif
