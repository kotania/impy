c-----------------------------------------------------------------------     
      subroutine EposInput(nevto,isho)
c-----------------------------------------------------------------------     
c Read informations (new options or parameter change) in the file
c "epos.param". The unit "ifop" is used in aread. If not used, it will
c use the default value of all parameters.
c-----------------------------------------------------------------------     
      include "epos.inc"   
      nopen=0
      ifop=35
      open(unit=ifop,file='example.param',status='old')
      call aread
      close(ifop)
c for main program
      nevto  = nevent
      isho   = ish
      end


      subroutine InitializeEpos(seed, emax, datpath, lpath, ifram, 
     &   ippdg, itpdg, iapro, izpro, iatar, iztar, idebug, iou)
c-----------------------------------------------------------------------
c General initialization of EPOS
c-----------------------------------------------------------------------      
      include "epos.inc"
      real seed, emax
      integer lpath, ifram, idpro, idtar, iapro, izpro, iatar, 
     &  iztar, idebug, iou
      character(*) datpath
      
      seedi=seed   !seed for random number generator: at start program
      seedj=seed   !seed for random number generator: for first event

c Initialize decay of particles (all unstable decay)
      nrnody=0

      call LHCparameters        !LHC tune for EPOS
      isigma=2                  !use analytic cross section for nuclear xs
      ionudi=1

c      isigma=0              !do not print out the cross section on screen
c      ionudi=3              !count diffraction without excitation as elastic

      iframe=10 + ifram           !nucleon-nucleon frame (12=target)
      iecho=0                     !"silent" reading mode

      nfnnx=lpath   
      fnnx=datpath                    ! path to main epos subdirectory
      print *, datpath, lpath
      nfnii=lpath + 10                            ! epos tab file name lenght
      fnii=fnnx(1:nfnnx) // "epos.initl"  ! epos tab file name
      nfnid=lpath + 10
      fnid=fnnx(1:nfnnx) // "epos.inidi"
      nfnie=lpath + 10
      fnie=fnnx(1:nfnnx) // "epos.iniev"
      nfnrj=lpath + 10
      fnrj=fnnx(1:nfnnx) // "epos.inirj"       !'.lhc' is added a the end of the file name in ainit if LHCparameters is called
      nfncs=lpath + 10
      fncs=fnnx(1:nfnnx) // "epos.inics"       !'.lhc' is added a the end of the file name in ainit if LHCparameters is called

c Debug
      ish=idebug       !debug level
      ifch=iou      !debug output (screen)
c      ifch=31    !debug output (file)
c      fnch="epos.debug"
c      nfnch=index(fnch,' ')-1
c      open(ifch,file=fnch(1:nfnch),status='unknown')


      nevent = 1  !number of events
      modsho = 1  !printout every modsho events

      ecms=emax  !center of mass energy in GeV/c2
      
      idproj = idtrafo("pdg","nxs",ippdg)
      laproj = izpro      !proj Z
      maproj = iapro      !proj A
      idtarg = idtrafo("pdg","nxs",itpdg)
      latarg = iztar      !targ Z
      matarg = iatar      !targ A

      istmax = 0      !only final particles (istmax=1 includes mother particles)

      End


      subroutine InitEposEvt(ecm, ela, idpro, idtar, iapro, 
     &   izpro, iatar, iztar)
c-----------------------------------------------------------------------
c Initialization to be called after changing the energy or beam
c configuration
c define either ecm < 0 and ela > 0 or ecm > 0 and ela < 0
c-----------------------------------------------------------------------      
      include "epos.inc"
      engy = -1.
      ecms = -1.
      elab = -1.
      ekin = -1.
      pnll = -1.

      ecms=ecm  !center of mass energy in GeV/c2
      elab=ela  ! lab energy

      idprojin = idtrafo("pdg","nxs",idpro)
      if (idpro.ne.2212) izpro = -1
      laproj = izpro      !proj Z
      maproj = iapro      !proj A
      idtargin = idtrafo("pdg","nxs",idtar)
      latarg = iztar      !targ Z
      matarg = iatar      !targ A

      istmax = 0      !only final particles (istmax=1 includes mother particles)
      call ainit()
      End

      subroutine SetStable(idpdg)
c-----------------------------------------------------------------------
c Sets particles as stable
c-----------------------------------------------------------------------

      include "epos.inc"

      nrnody=nrnody+1
      nody(nrnody)=idtrafo("pdg","nxs",idpdg)

      End

      subroutine SetUnstable(idpdg)
c-----------------------------------------------------------------------
c Sets particles as stable
c-----------------------------------------------------------------------

      include "epos.inc"
      
      newcount = 1
      do i = 1, nrnody
C        print *, 'i=',i, idtrafo("nxs","pdg", nody(i))
        if (abs(idtrafo("nxs","pdg", nody(i))).ne.abs(idpdg)) then
          nody(newcount) = nody(i)
          newcount = newcount + 1
        end if
      end do
      nrnody = newcount

      End

      real function GetCharge(idpdg)
c-----------------------------------------------------------------------
c Returns charge for partile with PDG ID
c-----------------------------------------------------------------------
      integer idpdg

      call idchrg(idtrafo("pdg","nxs",idpdg),GetCharge)
      return 

      End

c-----------------------------------------------------------------------
      subroutine xsection(xsigtot,xsigine,xsigela,xsigdd,xsigsd
     &    ,xsloela)
c-----------------------------------------------------------------------
c     cross section function
c-----------------------------------------------------------------------

      implicit none
      include 'epos.inc'
      double precision xsigtot,xsigine,xsigela,xsigdd,xsigsd
     &                ,xsloela

Cf2py intent(out) xsigtot,xsigine,xsigela,xsigdd,xsigsd,xsloela

      xsigtot   = dble( sigtot   )
      xsigine   = dble( sigine   )
      xsigela   = dble( sigela   )
      xsigdd    = dble( sigdd    )
      xsigsd    = dble( sigsd    )
      xsloela   = dble( sloela   )
c Nuclear cross section only if needed
      ! xsigtot = 0d0
      ! xsigine = 0d0
      ! xsigela = 0d0
      if(maproj.gt.1.or.matarg.gt.1)then
        if(model.eq.1)then
          call crseaaEpos(sigtotaa,sigineaa,sigcutaa,sigelaaa)
        else
          call crseaaModel(sigtotaa,sigineaa,sigcutaa,sigelaaa)
        endif
        xsigtot = dble( sigtotaa )
        xsigine = dble( sigineaa )
        xsigela = dble( sigelaaa )
      endif

      return
      end
