%define dropdir %(pkg-config libpcsclite --variable=usbdropdir)

Name:           openct
Version:        0.6.19
Release:        4%{?dist}
Summary:        Middleware framework for smart card terminals

Group:          System Environment/Libraries
License:        LGPLv2+
URL:            http://www.opensc-project.org/openct/
Source0:        http://www.opensc-project.org/files/openct/%{name}-%{version}.tar.gz
Source1:        %{name}.init
Source2:        %{name}.sysconfig
Patch1:         %{name}-0.6.19-nosleep.patch
Patch2:         %{name}-0.6.16-udevadm.patch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  pcsc-lite-devel >= 1.3.0
BuildRequires:  libusb-devel
BuildRequires:  libtool-ltdl-devel
BuildRequires:  doxygen
Requires:       ctapi-common%{?_isa}
# 098 for some keywords in shipped rules, see etc/openct.udev for more info
Requires:       udev >= 098
Requires(post): /sbin/chkconfig /sbin/service
Requires(post): /sbin/ldconfig
Requires(preun): /sbin/chkconfig /sbin/service
Requires(postun): /sbin/ldconfig /sbin/service

%description
OpenCT implements drivers for several smart card readers.  It comes as
driver in ifdhandler format for PC/SC-Lite, as CT-API driver, or as a
small and lean middleware, so applications can use it with minimal
overhead.  OpenCT also has a primitive mechanism to export smart card
readers to remote machines via TCP/IP.

%package        devel
Summary:        OpenCT development files
Group:          Development/Libraries
Requires:       %{name} = %{version}-%{release}
Requires:       pkgconfig

%description    devel
%{summary}.

%package     -n pcsc-lite-%{name}
Summary:        OpenCT PC/SC Lite driver
Group:          System Environment/Daemons
Requires:       pcsc-lite >= 1.2.0
Provides:       pcsc-ifd-handler
Provides:       %{name}-pcsc-lite = %{version}-%{release}
Requires(post): pcsc-lite /sbin/service
Requires(postun): /sbin/service

%description -n pcsc-lite-%{name}
The OpenCT PC/SC Lite driver makes smart card readers supported by
OpenCT available for PC/SC Lite.


%prep
%setup -q
%patch1 -p1 -b .nosleep
%patch2 -p1 -b .udevadm

# fix lib64 std rpaths and other weirdness
sed -i -e 's|/lib /usr/lib\b|/%{_lib} %{_libdir}|' \
       -e 's|^usrsbindir=.*$|usrsbindir="%{_sbindir}"|' \
       -e 's|^usrlibdir=.*$|usrlibdir="%{_libdir}"|' configure 
sed -i -e 's|^\([A-Z]\)|# \1|' etc/reader.conf.in


%build
# openct uses some gnu extensions
export CFLAGS="$RPM_OPT_FLAGS -D_GNU_SOURCE"
%configure \
    --disable-static \
    --enable-usb \
    --enable-pcsc \
    --enable-doc \
    --enable-api-doc \
    --with-udev=/lib/udev \
    --with-bundle=%{dropdir}
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
install -dm 755 $RPM_BUILD_ROOT/lib/udev
make install DESTDIR=$RPM_BUILD_ROOT

install -dm 755 $RPM_BUILD_ROOT%{_libdir}/ctapi
mv $RPM_BUILD_ROOT%{_libdir}/{libopenctapi.so,ctapi}

install -Dpm 644 etc/openct.udev \
    $RPM_BUILD_ROOT%{_sysconfdir}/udev/rules.d/60-openct.rules

install -pm 644 etc/openct.conf $RPM_BUILD_ROOT%{_sysconfdir}/openct.conf

install -Dpm 755 %{SOURCE1} $RPM_BUILD_ROOT%{_initddir}/openct

install -Dpm 644 %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/openct

so=$(find $RPM_BUILD_ROOT%{dropdir} -name \*.so | sed "s|^$RPM_BUILD_ROOT||")
sed -i -e "s|\\(LIBPATH\\s*\\).*|\\1$so|" etc/reader.conf
install -Dpm 644 etc/reader.conf \
    $RPM_BUILD_ROOT%{_sysconfdir}/reader.conf.d/%{name}.conf

install -dm 755 $RPM_BUILD_ROOT%{_localstatedir}/run/openct
touch $RPM_BUILD_ROOT%{_localstatedir}/run/openct/status
chmod 644 $RPM_BUILD_ROOT%{_localstatedir}/run/openct/status

rm -f $RPM_BUILD_ROOT%{_libdir}/{*.la,openct-ifd.so}

mkdir apidocdir
mv $RPM_BUILD_ROOT%{_datadir}/doc/%{name}/api apidocdir
mv -T $RPM_BUILD_ROOT%{_datadir}/doc/%{name} docdir

%clean
rm -rf $RPM_BUILD_ROOT


%post
/sbin/ldconfig
/sbin/chkconfig --add openct

%preun
if [ $1 -eq 0 ] ; then
    /sbin/service openct stop >/dev/null 2>&1 || :
    /sbin/chkconfig --del openct
fi

%postun
/sbin/ldconfig
if [ $1 -gt 0 ] ; then
    /sbin/service openct try-restart >/dev/null || :
fi

%post -n pcsc-lite-%{name}
if [ $1 -eq 1 ] ; then
    /sbin/service pcscd try-restart >/dev/null 2>&1 || :
fi

%postun -n pcsc-lite-%{name}
/sbin/service pcscd try-restart >/dev/null 2>&1 || :


%files
%defattr(-,root,root,-)
%doc LGPL-2.1 TODO NEWS
%doc docdir/*
%config(noreplace) %{_sysconfdir}/openct.conf
%config(noreplace) %{_sysconfdir}/sysconfig/openct
%config(noreplace) %{_sysconfdir}/udev/rules.d/*openct.rules
%{_initddir}/openct
%{_bindir}/openct-tool
%{_sbindir}/ifdhandler
%{_sbindir}/ifdproxy
%{_sbindir}/openct-control
/lib/udev/openct_pcmcia
/lib/udev/openct_serial
/lib/udev/openct_usb
%{_libdir}/ctapi/libopenctapi.so
%{_libdir}/libopenct.so.*
%dir %{_localstatedir}/run/openct/
%ghost %{_localstatedir}/run/openct/status
%{_mandir}/man1/openct-tool.1*

%files devel
%defattr(-,root,root,-)
%doc apidocdir/*
%{_includedir}/openct/
%{_libdir}/pkgconfig/libopenct.pc
%{_libdir}/libopenct.so

%files -n pcsc-lite-%{name}
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/reader.conf.d/%{name}.conf
%{dropdir}/openct-ifd.bundle/


%changelog
* Mon May 31 2010 Tomas Mraz <tmraz@redhat.com> - 0.6.19-4
- One more init script typo fix (#575816)

* Wed May 19 2010 Tomas Mraz <tmraz@redhat.com> - 0.6.19-3
- More init script fixes

* Wed Feb  3 2010 Tomas Mraz <tmraz@redhat.com> - 0.6.19-2
- Minor spec file and init script fixes (#561391)

* Mon Jan 11 2010 Tomas Mraz <tmraz@redhat.com> - 0.6.19-1
- Update to latest upstream

* Tue Nov 10 2009 Tomas Mraz <tmraz@redhat.com> - 0.6.18-1
- Update to latest upstream
- Do not use file dependency (#533939)

* Thu Sep 24 2009 Tomas Mraz <tmraz@redhat.com> - 0.6.17-1
- Update to latest upstream

* Sat Jul 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.16-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Jun 15 2009 Tomas Mraz <tmraz@redhat.com> - 0.6.16-1
- Update to latest upstream
- Prefer udevname to udevinfo (#506163)

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.15-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Jan 20 2009 Tomas Mraz <tmraz@redhat.com> - 0.6.15-3
- fix usrsbindir in configure (fix by Oskari Saarenmaa) (#480756)

* Tue Sep  2 2008 Tomas Mraz <tmraz@redhat.com> - 0.6.15-1
- Update to latest upstream

* Wed Feb 13 2008 Hans de Goede <j.w.r.degoede@hhs.nl> 0.6.14-4
- Fix building with latest glibc
- Rebuild for gcc-4.3  

* Fri Oct 12 2007 Ville Skyttä <ville.skytta at iki.fi> - 0.6.14-3
- Fix init script exit status when stopping already stopped service (#247009).

* Fri Sep 21 2007 Ville Skyttä <ville.skytta at iki.fi> - 0.6.14-2
- Drop "sleep 0.1" from udev rule (#287871).

* Thu Aug 30 2007 Ville Skyttä <ville.skytta at iki.fi> - 0.6.14-1
- 0.6.14.

* Tue Aug 28 2007 Ville Skyttä <ville.skytta at iki.fi> - 0.6.13-1
- 0.6.13.

* Thu Aug 16 2007 Ville Skyttä <ville.skytta at iki.fi> - 0.6.12-2
- License: LGPLv2+

* Tue Jul 17 2007 Ville Skyttä <ville.skytta at iki.fi> - 0.6.12-1
- 0.6.12.
- Add Default-Start and Default-Stop to init script.

* Sat Jun 30 2007 Ville Skyttä <ville.skytta at iki.fi> - 0.6.12-0.1.pre3
- 0.6.12-pre3.
- Add LSB comment block to init script.
- Use vanilla upstream udev rules, requires udev >= 098.

* Sat May 26 2007 Ville Skyttä <ville.skytta at iki.fi> - 0.6.12-0.1.pre2
- 0.6.12-pre2.

* Wed Nov 22 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.11-2
- Don't run autotools during build.

* Wed Nov 22 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.11-1
- 0.6.11.

* Sat Nov 11 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.10-1
- 0.6.10, udev rules fixed upstream.

* Mon Oct 16 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.9-3
- Fix udev rules for newer udev versions (#210868).

* Mon Oct  2 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.9-2
- Rebuild.

* Fri Sep 22 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.9-1
- 0.6.9.

* Mon Aug 28 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.8-2
- Rebuild.

* Tue Jun 20 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.8-1
- 0.6.8.

* Thu May 25 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.7-3
- Make installation more multilib friendly.

* Sat May  6 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.7-2
- Install CT-API module into %%{_libdir}/ctapi, add dependency on it (#190903).
- Update URL.

* Thu May  4 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.7-1
- 0.6.7.

* Wed Apr 26 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.7-0.1.rc4
- 0.6.7-rc4.
- Re-enable PCSC hotplug in pcsc-lite subpackage.
- Include license text.

* Sat Apr 22 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.7-0.1.rc1
- 0.6.7-rc1, udev rules and reader.conf included upstream.

* Mon Mar  6 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.6-5
- Rebuild with new pcsc-lite.

* Wed Feb 15 2006 Ville Skyttä <ville.skytta at iki.fi> - 0.6.6-4
- Avoid standard rpaths on lib64 archs.

* Mon Nov 28 2005 Ville Skyttä <ville.skytta at iki.fi> - 0.6.6-3
- Adapt to udev, drop old hotplug support.
- Init script improvements: incoming events don't start explicitly stopped
  daemons, improved status output.
- Init script is not a config file.

* Sun Sep 11 2005 Ville Skyttä <ville.skytta at iki.fi> - 0.6.6-2
- 0.6.6.
- Improve description.
- Don't ship static libs.

* Tue May 17 2005 Ville Skyttä <ville.skytta at iki.fi> - 0.6.5-2
- 0.6.5.

* Wed May 11 2005 Ville Skyttä <ville.skytta at iki.fi> - 0.6.5-0.2.rc2
- 0.6.5rc2, patches applied upstream.

* Fri Apr  7 2005 Michael Schwendt <mschwendt[AT]users.sf.net> - 0.6.2-3
- rebuilt

* Tue Feb 22 2005 Ville Skyttä <ville.skytta at iki.fi> - 0:0.6.2-2
- Comment out CardMan 3121 (CCID) in default config too, the "ccid" driver
  package works a lot better with it.

* Tue Feb  1 2005 Ville Skyttä <ville.skytta at iki.fi> - 0:0.6.2-1
- Disable CardMan driver in default configs, too unreliable at the moment.

* Wed Nov  3 2004 Ville Skyttä <ville.skytta at iki.fi> - 0:0.6.2-0.fdr.1
- Update to 0.6.2, eToken bundle patch applied upstream.
- Make scriptlet dependencies more granular.

* Tue Aug 17 2004 Ville Skyttä <ville.skytta at iki.fi> - 0:0.6.1-0.fdr.2
- Split PC/SC Lite stuff into the pcsc-lite-openct subpackage, use symlinks
  to avoid packaging the same .so many times.
- Install reader.conf snippet for pcsc-lite.
- Patch to make eToken PRO hotplug work with PC/SC Lite.
- Exclude more unneeded files from docs and -devel.
- Disable dependency tracking to speed up the build.

* Thu Jul 22 2004 Ville Skyttä <ville.skytta at iki.fi> - 0:0.6.1-0.fdr.1
- Update to 0.6.1 (preview).

* Thu Jul  1 2004 Ville Skyttä <ville.skytta at iki.fi> - 0:0.6.0-0.fdr.0.1.alpha
- Update to 0.6.0-alpha.

* Fri Apr 16 2004 Ville Skyttä <ville.skytta at iki.fi> - 0:0.5.0-0.fdr.6
- Init script improvements.

* Wed Feb  4 2004 Ville Skyttä <ville.skytta at iki.fi> - 0:0.5.0-0.fdr.5
- Autostart service in runlevels 2-5.

* Thu Jan 29 2004 Ville Skyttä <ville.skytta at iki.fi> - 0:0.5.0-0.fdr.4
- More init script fine tuning.

* Mon Jan 12 2004 Ville Skyttä <ville.skytta at iki.fi> - 0:0.5.0-0.fdr.3
- Init script improvements.

* Mon Dec 29 2003 Ville Skyttä <ville.skytta at iki.fi> - 0:0.5.0-0.fdr.2
- Include init script and a sysconfig file.
- Improve summary and description.

* Mon Nov 24 2003 Ville Skyttä <ville.skytta at iki.fi> - 0:0.5.0-0.fdr.1
- Update to 0.5.0.

* Fri Nov 14 2003 Ville Skyttä <ville.skytta at iki.fi> - 0:0.1.0-0.fdr.2
- Create /var/run/openct/status to avoid OpenSC errors.

* Tue Aug 19 2003 Ville Skyttä <ville.skytta at iki.fi> - 0:0.1.0-0.fdr.1
- First build.
