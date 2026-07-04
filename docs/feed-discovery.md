# Feed-discovery check against the Mobility Database

Run 2026-06-19. Source: mobilitydatabase.org catalog CSV.

This checks whether the feed URL each agency is tracked on still appears in the Mobility Database, and where it doesn't, proposes the catalog feed that looks like the same agency. Candidates are suggestions to verify by hand, not automatic edits.

> Scope: this run covered a 63-agency subset (the California / Trillium cohort), not the full ~1,100-agency registry. The counts below are for that subset.

- **0** agencies look **replaced**: the catalog lists a different download URL for the same agency.
- **0** agencies have **no catalog match** on name or URL.
- **63** agencies are still on their **listed URL**: the link is canonical, so any staleness is at the source, not a wrong URL here.

## Still on the listed URL — staleness is at the source

The Mobility Database lists the same download URL we already track, so there is no newer canonical feed to switch to. A feed here that is also expired means the agency or its vendor stopped refreshing the export, not that the link moved.

- Alhambra Community Transit (`alhambra-community-transit`): http://data.trilliumtransit.com/gtfs/alhambra-ca-us/alhambra-ca-us.zip
- Arcadia Transit (`arcadia-transit`): http://data.trilliumtransit.com/gtfs/arcadia-ca-us/arcadia-ca-us.zip
- Arvin Transit (`arvin-transit`): http://data.trilliumtransit.com/gtfs/arvin-ca-us/arvin-ca-us.zip
- Auburn Transit (`auburn-transit`): http://data.trilliumtransit.com/gtfs/auburntransit-ca-us/auburntransit-ca-us.zip
- Avalon Transit (`avalon-transit`): http://data.trilliumtransit.com/gtfs/avalon-ca-us/avalon-ca-us.zip
- Baldwin Park Transit (`baldwin-park-transit`): http://data.trilliumtransit.com/gtfs/baldwinpark-ca-us/baldwinpark-ca-us.zip
- Calabasas Transit System (`calabasas-transit-system`): http://data.trilliumtransit.com/gtfs/calabasas-ca-us/calabasas-ca-us.zip
- Carson Circuit (`carson-circuit`): http://data.trilliumtransit.com/gtfs/carson-ca-us/carson-ca-us.zip
- Catalina Flyer (`catalina-flyer`): http://data.trilliumtransit.com/gtfs/catalinaflyer-ca-us/catalinaflyer-ca-us.zip
- City of Bell (La Campana) (`city-of-bell-la-campana`): http://data.trilliumtransit.com/gtfs/lacampana-ca-us/lacampana-ca-us.zip
- City of Tracy (TRACER) (`city-of-tracy-tracer`): http://data.trilliumtransit.com/gtfs/tracy-ca-us/tracy-ca-us.zip
- Clovis Transit (`clovis-transit`): http://data.trilliumtransit.com/gtfs/clovistransit-ca-us/clovistransit-ca-us.zip
- Compton Renaissance (`compton-renaissance`): https://raw.githubusercontent.com/LACMTA/los-angeles-regional-gtfs/main/compton-ca-us/compton-ca-us.zip
- Cudahy Area Rapid Transit (`cudahy-area-rapid-transit`): http://data.trilliumtransit.com/gtfs/cudahy-ca-us/cudahy-ca-us.zip
- Duarte Transit (`duarte-transit`): http://data.trilliumtransit.com/gtfs/duartetransit-ca-us/duartetransit-ca-us.zip
- El Monte Transit (`el-monte-transit`): http://data.trilliumtransit.com/gtfs/elmonte-ca-us/elmonte-ca-us.zip
- El Segundo Transportation (`el-segundo-transportation`): http://data.trilliumtransit.com/gtfs/elsegundo-ca-us/elsegundo-ca-us.zip
- Emery Go-Round (`emery-go-round`): http://data.trilliumtransit.com/gtfs/emerygoround-ca-us/emerygoround-ca-us.zip
- Glenn Transit Service (`glenn-transit-service`): http://data.trilliumtransit.com/gtfs/glenn-ca-us/glenn-ca-us.zip
- Go West Shuttle (`go-west-shuttle`): http://data.trilliumtransit.com/gtfs/westcovina-ca-us/westcovina-ca-us.zip
- GTrans (`gtrans`): http://data.trilliumtransit.com/gtfs/gtrans-ca-us/gtrans-ca-us.zip
- Guadalupe Flyer (`guadalupe-flyer`): http://data.trilliumtransit.com/gtfs/guadalupeflyer-ca-us/guadalupeflyer-ca-us.zip
- Huntington Park Express (`huntington-park-express-2648`): https://www.hpca.gov/DocumentCenter/View/11702
- Kings Area Rural Transit (`kings-area-rural-transit`): http://data.trilliumtransit.com/gtfs/kcapta-ca-us/kcapta-ca-us.zip
- La Puente LINK (`la-puente-link`): http://data.trilliumtransit.com/gtfs/lapuente-ca-us/lapuente-ca-us.zip
- Merced County Transit (The Bus) (`merced-county-transit-the-bus`): http://data.trilliumtransit.com/gtfs/mercedthebus-ca-us/mercedthebus-ca-us.zip
- Modesto Area Express (`modesto-area-express`): https://www.modestoareaexpress.com/preview-gtfs.zip
- Montebello Bus Lines (`montebello-bus-lines`): http://data.trilliumtransit.com/gtfs/montebello-ca-us/montebello-ca-us.zip
- Nevada County Connects (Gold Country Stage) (`nevada-county-connects-gold-country-stage`): http://data.trilliumtransit.com/gtfs/goldcountrystage-ca-us/goldcountrystage-ca-us.zip
- Norwalk Transit System (NTS) (`norwalk-transit-system-nts`): http://data.trilliumtransit.com/gtfs/nts-ca-us/nts-ca-us.zip
- Petaluma Transit (`petaluma-transit`): http://data.trilliumtransit.com/gtfs/petalumatransit-petaluma-ca-us/petalumatransit-petaluma-ca-us.zip
- Porterville Transit (`porterville-transit`): http://data.trilliumtransit.com/gtfs/porterville-ca-us/porterville-ca-us.zip
- Redding Area Bus Authority (`redding-area-bus-authority`): https://rabagtfs.z5.web.core.windows.net/rabagtfs.zip
- Redding Area Bus Authority (RABA) (`redding-area-bus-authority-raba`): http://data.trilliumtransit.com/gtfs/redding-ca-us/redding-ca-us.zip
- Reds Meadow Shuttle (`devils-postpile-national-monument`): https://www.nps.gov/external-resources/gtfs/depo/reds-meadow-shuttle.zip
- Redwood Coast Transit (RCT) (`redwood-coast-transit-rct`): http://data.trilliumtransit.com/gtfs/delnorte-ca-us/delnorte-ca-us.zip
- reLAXsan (`relaxsan`): https://relaxsan.s3.amazonaws.com/gtfs.zip
- Ridgecrest Transit (`ridgecrest-transit`): https://www.ridgecrest-ca.gov/DocumentCenter/View/7499/Ridgecrest_gtfszip
- Ridgerunner (`ridgerunner`): http://data.trilliumtransit.com/gtfs/cityofridgecrest-ca-us/cityofridgecrest-ca-us.zip
- Rio Vista Delta Breeze (`rio-vista-delta-breeze`): http://data.trilliumtransit.com/gtfs/riovista-ca-us/riovista-ca-us.zip
- San Benito County Express (SBCE) (`san-benito-county-express-sbce`): http://data.trilliumtransit.com/gtfs/sanbenitocounty-ca-us/sanbenitocounty-ca-us.zip
- San Juan Capistrano Free Weekend Trolley (`san-juan-capistrano-free-weekend-trolley`): http://data.trilliumtransit.com/gtfs/sanjuancapistrano-ca-us/sanjuancapistrano-ca-us.zip
- San Leandro Links (`san-leandro-links`): http://data.trilliumtransit.com/gtfs/sanleandro-ca-us/sanleandro-ca-us.zip
- Santa Maria Area Transit (`santa-maria-area-transit`): http://data.trilliumtransit.com/gtfs/smat-ca-us/smat-ca-us.zip
- Santa Rosa CityBus (`santa-rosa-citybus-1986`): https://www.srcity.org/DocumentCenter/View/38683/Santa_Rosa_GTFS
- Sierra Madre Gateway Coach (`sierra-madre-gateway-coach`): http://data.trilliumtransit.com/gtfs/sierramadre-ca-us/sierramadre-ca-us.zip
- Simi Valley Transit (`simi-valley-transit`): http://data.trilliumtransit.com/gtfs/simivalley-ca-us/simivalley-ca-us.zip
- Sonoma County Airport Express (`sonoma-county-airport-express`): http://data.trilliumtransit.com/gtfs/airportexpressinc-ca-us/airportexpressinc-ca-us.zip
- South County Transit Link (`south-county-transit-link`): http://data.trilliumtransit.com/gtfs/southcountytransitlink-ca-us/southcountytransitlink-ca-us.zip
- Spirit Bus (`spirit-bus`): http://data.trilliumtransit.com/gtfs/montereypark-ca-us/montereypark-ca-us.zip
- Stanislaus Regional Transit (StaRT) (`stanislaus-regional-transit-start`): http://data.trilliumtransit.com/gtfs/stanislaus-ca-us/stanislaus-ca-us.zip
- Stanislaus Regional Transit Authority (`stanislaus-regional-transit-authority`): https://data.trilliumtransit.com/gtfs/stanrta-ca-us/stanrta-ca-us--flex-v2.zip
- Stanislaus Regional Transit Authority (StanRTA) (`stanislaus-regional-transit-authority-stanrta`): https://www.stanrta.org/DocumentCenter/View/609/preview-gtfs.zip
- SunLine Transit Agency (`sunline-transit-agency`): http://www.sunline.org/transit/google_transit.zip
- Taft Area Transit (`taft-area-transit`): http://data.trilliumtransit.com/gtfs/taft-ca-us/taft-ca-us.zip
- Tehama Rural Area Express (TRAX), Susanville Indian Rancheria Public Transportation Program (`tehama-rural-area-express-trax-susanville-indian-rancheria-public-transportation-program`): http://data.trilliumtransit.com/gtfs/tehama-ca-us/tehama-ca-us.zip
- Thousand Oaks Transit (`thousand-oaks-transit`): http://data.trilliumtransit.com/gtfs/thousandoaks-ca-us/thousandoaks-ca-us.zip
- Thousand Oaks Transit - Kanan Shuttle (`thousand-oaks-transit-kanan-shuttle`): https://data.trilliumtransit.com/gtfs/kananshuttle-ca-us/kananshuttle-ca-us.zip
- Trinity Transit (`trinity-transit`): http://data.trilliumtransit.com/gtfs/weaverville-ca-us/weaverville-ca-us.zip
- Union City Transit (`union-city-transit`): https://data.trilliumtransit.com/gtfs/unioncity-ca-us/unioncity-ca-us.zip
- University of California Berkeley Shuttle (Bear Transit) (`university-of-california-berkeley-shuttle-bear-transit`): http://data.trilliumtransit.com/gtfs/beartransit-ca-us/beartransit-ca-us.zip
- Ventura County Transportation Commission (`ventura-county-transportation-commission`): http://data.trilliumtransit.com/gtfs/vctc-ca-us/vctc-ca-us.zip
- Yosemite Area Regional Transportation System (YARTS) (`yosemite-area-regional-transportation-system-yarts`): http://data.trilliumtransit.com/gtfs/yosemite-ca-us/yosemite-ca-us.zip
