import { keepPreviousData, useQuery } from "@tanstack/react-query";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Accordion,
  Alert,
  Badge,
  Button,
  ButtonGroup,
  Card,
  Col,
  Container,
  Form,
  Pagination,
  Row,
  Spinner,
} from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";
import { useNavigate, useSearchParams } from "react-router-dom";

import type {
  CountryListItemSchemaOut,
  PagedImageThumbnailSchemaOut,
  PersonReadOutSchema,
  PetReadSchemaOut,
  SubdivisionListItemSchemaOut,
} from "../api";

import {
  getAllPeople,
  getAllPets,
  listCountries,
  listImages,
  listPossibleCountryCities,
  listSubdivisions,
  locationGetSubLocations,
} from "../api";
import ThemedSelect from "../components/common/ThemedSelect";
import ImageWall from "../components/image/ImageWall";
import { useAuth } from "../hooks/useAuth";
import { useDebounce } from "../hooks/useDebounce";

// Define the form inputs based on backend filter schemas
interface ImageFilterFormInputs {
  is_starred: boolean;
  is_deleted: boolean;
  people_ids: { value: number; label: string }[]; // For react-select
  pets_ids: { value: number; label: string }[]; // For react-select
  country_code: { value: string; label: string } | null; // For react-select
  subdivision_code: { value: string; label: string } | null; // For react-select
  city: string; // Text input with autocomplete suggestions
  sub_location: string; // Text input with autocomplete suggestions
  date_start: string; // YYYY-MM-DD
  date_end: string; // YYYY-MM-DD
  year: number | null;
  month: number | null;
  day: number | null;
  sort_by: "created_at" | "-created_at" | "updated_at" | "-updated_at" | "pk" | "title" | "-title";
  require_all: boolean;
}

// Helper to fetch all paginated data from an API endpoint
async function fetchAllPaginatedData<T, QueryParams extends object = {}>(
  fetchFn: (options?: {
    query?: QueryParams & { limit?: number; offset?: number };
    throwOnError?: boolean;
  }) => Promise<{ data?: { items?: T[]; count: number } | undefined }>,
  initialQuery: QueryParams = {} as QueryParams,
  pageSize: number = 100, // A reasonable page size for fetching all options
): Promise<T[]> {
  let allItems: T[] = [];
  let offset = 0;
  let hasMore = true;

  while (hasMore) {
    try {
      const response = await fetchFn({
        query: { ...initialQuery, limit: pageSize, offset: offset } as QueryParams & {
          limit?: number;
          offset?: number;
        },
        throwOnError: true,
      });
      const data = response.data;

      if (data && data.items) {
        allItems = allItems.concat(data.items);
        if (data.items.length < pageSize || allItems.length >= data.count) {
          hasMore = false;
        } else {
          offset += pageSize;
        }
      } else {
        hasMore = false;
      }
    } catch (error) {
      console.error("Failed to fetch paginated data:", error);
      hasMore = false;
    }
  }

  return allItems;
}

const ImageGalleryPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { profile } = useAuth();

  // Pagination states
  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = profile?.items_per_page || 30; // Default to 30 if profile not loaded
  const offset = (currentPage - 1) * pageSize;

  // Form management with react-hook-form
  const {
    control,
    watch,
    setValue,
    reset,
    formState: { isDirty },
  } = useForm<ImageFilterFormInputs>({
    defaultValues: {
      is_starred: searchParams.get("is_starred") === "true",
      is_deleted: searchParams.get("is_deleted") === "true",
      people_ids: [],
      pets_ids: [],
      country_code: null,
      subdivision_code: null,
      city: searchParams.get("city") || "",
      sub_location: searchParams.get("sub_location") || "",
      date_start: searchParams.get("date_start") || "",
      date_end: searchParams.get("date_end") || "",
      year: searchParams.get("year") ? parseInt(searchParams.get("year")!, 10) : null,
      month: searchParams.get("month") ? parseInt(searchParams.get("month")!, 10) : null,
      day: searchParams.get("day") ? parseInt(searchParams.get("day")!, 10) : null,
      sort_by: (searchParams.get("sort_by") || "pk") as ImageFilterFormInputs["sort_by"],
      require_all: searchParams.get("require_all") === "true", // Add this line
    },
  });

  // Watch form values for dependent queries and UI updates
  // Only watch the primitive or memoized values to keep dependency arrays stable
  const watchedIsStarred = watch("is_starred");
  const watchedIsDeleted = watch("is_deleted");
  const watchedCity = watch("city");
  const watchedSubLocation = watch("sub_location");
  const watchedDateStart = watch("date_start");
  const watchedDateEnd = watch("date_end");
  const watchedYear = watch("year");
  const watchedMonth = watch("month");
  const watchedDay = watch("day");
  const watchedSortBy = watch("sort_by");
  const watchedRequireAll = watch("require_all");

  // For react-select values, watch their 'value' properties directly
  // This helps keep query keys stable and avoids unnecessary re-renders
  const watchedCountryValue = watch("country_code")?.value;
  const watchedSubdivisionValue = watch("subdivision_code")?.value;
  const watchedPeopleIdsValues = watch("people_ids").map((p) => p.value);
  const watchedPetsIdsValues = watch("pets_ids").map((p) => p.value);

  const debouncedCity = useDebounce(watchedCity, 500);
  const debouncedSubLocation = useDebounce(watchedSubLocation, 500);
  const debouncedDateStart = useDebounce(watchedDateStart, 300);
  const debouncedDateEnd = useDebounce(watchedDateEnd, 300);
  const debouncedYear = useDebounce(watchedYear, 300);
  const debouncedMonth = useDebounce(watchedMonth, 300);
  const debouncedDay = useDebounce(watchedDay, 300);

  const debouncedPeopleIds = useDebounce(watchedPeopleIdsValues.join(","), 300);
  const debouncedPetsIds = useDebounce(watchedPetsIdsValues.join(","), 300);

  // State for autocomplete suggestions visibility
  const [showCitySuggestions, setShowCitySuggestions] = useState<boolean>(false);
  const [showSubLocationSuggestions, setShowSubLocationSuggestions] = useState<boolean>(false);
  const cityAutocompleteRef = useRef<HTMLDivElement>(null);
  const subLocationAutocompleteRef = useRef<HTMLDivElement>(null);

  // --- API Calls for Filter Options ---

  // Countries
  const { data: countries = [], isLoading: isLoadingCountries } = useQuery<
    CountryListItemSchemaOut[],
    Error
  >({
    queryKey: ["countries"],
    queryFn: async () => {
      const response = await listCountries({ throwOnError: true });
      return response.data || [];
    },
    staleTime: 5 * 60 * 1000,
  });

  // Subdivisions (depends on selected country)
  const { data: subdivisions = [], isLoading: isLoadingSubdivisions } = useQuery<
    SubdivisionListItemSchemaOut[],
    Error
  >({
    queryKey: ["subdivisions", watchedCountryValue],
    queryFn: async () => {
      if (!watchedCountryValue) return [];
      const response = await listSubdivisions({
        query: { country_code: watchedCountryValue },
        throwOnError: true,
      });
      return response.data || [];
    },
    enabled: !!watchedCountryValue,
    staleTime: 5 * 60 * 1000,
  });

  // Cities (depends on selected country and subdivision)
  const { data: cities = [], isLoading: isLoadingCities } = useQuery<string[], Error>({
    queryKey: ["cities", watchedCountryValue, watchedSubdivisionValue],
    queryFn: async () => {
      if (!watchedCountryValue) return [];
      const queryParams: { country_code: string; subdivision_code?: string } = {
        country_code: watchedCountryValue,
      };
      if (watchedSubdivisionValue) {
        queryParams.subdivision_code = watchedSubdivisionValue;
      }
      const response = await listPossibleCountryCities({
        query: queryParams,
        throwOnError: true,
      });
      return response.data || [];
    },
    enabled: !!watchedCountryValue,
    staleTime: 5 * 60 * 1000,
  });

  // Sub-locations (depends on selected country, subdivision (maybe), and city)
  const { data: subLocations = [], isLoading: isLoadingSubLocations } = useQuery<string[], Error>({
    queryKey: ["subLocations", watchedCountryValue, watchedSubdivisionValue, debouncedCity],
    queryFn: async () => {
      if (!watchedCountryValue || !debouncedCity) return [];
      const queryParams: { country_code: string; city_name: string; subdivision_code?: string } = {
        country_code: watchedCountryValue,
        city_name: debouncedCity,
      };
      if (watchedSubdivisionValue) {
        queryParams.subdivision_code = watchedSubdivisionValue;
      }
      const response = await locationGetSubLocations({
        query: queryParams,
        throwOnError: true,
      });
      return response.data || [];
    },
    enabled: !!watchedCountryValue && !!debouncedCity,
    staleTime: 5 * 60 * 1000,
  });

  // All People (for filter dropdown)
  const { data: allPeople = [], isLoading: isLoadingAllPeople } = useQuery<
    PersonReadOutSchema[],
    Error
  >({
    queryKey: ["allPeople"],
    queryFn: () => fetchAllPaginatedData(getAllPeople, {}, 100),
    staleTime: 5 * 60 * 1000,
  });

  // All Pets (for filter dropdown)
  const { data: allPets = [], isLoading: isLoadingAllPets } = useQuery<PetReadSchemaOut[], Error>({
    queryKey: ["allPets"],
    queryFn: () => fetchAllPaginatedData(getAllPets, {}, 100),
    staleTime: 5 * 60 * 1000,
  });

  // --- Main Image List Query ---
  const {
    data: imagesData,
    isLoading: isLoadingImages,
    isError: isErrorImages,
    error: imagesError,
    isPlaceholderData,
  } = useQuery<PagedImageThumbnailSchemaOut, Error>({
    queryKey: [
      "images",
      currentPage,
      pageSize,
      watchedIsStarred,
      watchedIsDeleted,
      debouncedPeopleIds,
      debouncedPetsIds,
      watchedCountryValue,
      watchedSubdivisionValue,
      debouncedCity,
      debouncedSubLocation,
      debouncedDateStart,
      debouncedDateEnd,
      debouncedYear,
      debouncedMonth,
      debouncedDay,
      watchedSortBy,
      watchedRequireAll,
    ],
    queryFn: async ({ signal }) => {
      const query: {
        limit: number;
        offset: number;
        is_starred?: boolean;
        is_deleted?: boolean;
        people_ids?: number[];
        pets_ids?: number[];
        country_code?: string;
        subdivision_code?: string;
        city?: string;
        sub_location?: string;
        date_start?: string;
        date_end?: string;
        year?: number;
        month?: number;
        day?: number;
        sort_by?:
          | "created_at"
          | "-created_at"
          | "updated_at"
          | "-updated_at"
          | "pk"
          | "title"
          | "-title";
        require_all?: boolean;
      } = {
        limit: pageSize,
        offset: offset,
      };

      if (typeof watchedIsStarred === "boolean" && watchedIsStarred)
        query.is_starred = watchedIsStarred;
      if (typeof watchedIsDeleted === "boolean" && watchedIsDeleted)
        query.is_deleted = watchedIsDeleted;

      // Use debounced values for arrays by converting back to numbers
      const debouncedPeopleArray = debouncedPeopleIds
        ? debouncedPeopleIds
            .split(",")
            .map(Number)
            .filter((n) => !isNaN(n))
        : [];
      const debouncedPetsArray = debouncedPetsIds
        ? debouncedPetsIds
            .split(",")
            .map(Number)
            .filter((n) => !isNaN(n))
        : [];

      if (debouncedPeopleArray.length > 0) query.people_ids = debouncedPeopleArray;
      if (debouncedPetsArray.length > 0) query.pets_ids = debouncedPetsArray;
      if (watchedCountryValue) query.country_code = watchedCountryValue;
      if (watchedSubdivisionValue) query.subdivision_code = watchedSubdivisionValue;
      if (debouncedCity) query.city = debouncedCity;
      if (debouncedSubLocation) query.sub_location = debouncedSubLocation;
      if (debouncedDateStart) query.date_start = debouncedDateStart;
      if (debouncedDateEnd) query.date_end = debouncedDateEnd;
      if (debouncedYear !== null) query.year = debouncedYear;
      if (debouncedMonth !== null && debouncedMonth >= 1 && debouncedMonth <= 12)
        query.month = debouncedMonth;
      if (debouncedDay !== null && debouncedDay >= 1 && debouncedDay <= 31)
        query.day = debouncedDay;
      if (watchedSortBy) query.sort_by = watchedSortBy;
      if (watchedRequireAll) query.require_all = watchedRequireAll;

      const response = await listImages({ query, throwOnError: true, signal });
      return response.data as PagedImageThumbnailSchemaOut;
    },
    placeholderData: keepPreviousData,
    staleTime: 30 * 1000,
  });

  const images = imagesData?.items || [];
  const totalImages = imagesData?.count || 0;
  const totalPages = totalImages ? Math.ceil(totalImages / pageSize) : 0;

  // --- Effects for managing form state and URL params ---

  // 1) Synchronize URL → form **only when searchParams changes**.
  useEffect(() => {
    const currentIsStarred = searchParams.get("is_starred") === "true";
    const currentIsDeleted = searchParams.get("is_deleted") === "true";
    const currentCity = searchParams.get("city") || "";
    const currentSubLocation = searchParams.get("sub_location") || "";
    const currentDateStart = searchParams.get("date_start") || "";
    const currentDateEnd = searchParams.get("date_end") || "";
    const currentYear = searchParams.get("year") ? parseInt(searchParams.get("year")!, 10) : null;
    const currentMonth = searchParams.get("month")
      ? parseInt(searchParams.get("month")!, 10)
      : null;
    const currentDay = searchParams.get("day") ? parseInt(searchParams.get("day")!, 10) : null;
    const currentPeopleIdsFromUrl = searchParams.getAll("people_ids").map(Number);
    const currentPetsIdsFromUrl = searchParams.getAll("pets_ids").map(Number);
    const currentCountryCodeFromUrl = searchParams.get("country_code");
    const currentSubdivisionCodeFromUrl = searchParams.get("subdivision_code");
    const currentSortBy = (searchParams.get("sort_by") ||
      "pk") as ImageFilterFormInputs["sort_by"];
    const currentRequireAll = searchParams.get("require_all") === "true";

    const initialPeopleSelections = currentPeopleIdsFromUrl.map((id) => ({
      value: id,
      label: "Loading…",
    }));
    const initialPetSelections = currentPetsIdsFromUrl.map((id) => ({
      value: id,
      label: "Loading…",
    }));

    const initialCountrySelection = currentCountryCodeFromUrl
      ? { value: currentCountryCodeFromUrl, label: "Loading…" }
      : null;
    const initialSubdivisionSelection = currentSubdivisionCodeFromUrl
      ? { value: currentSubdivisionCodeFromUrl, label: "Loading…" }
      : null;

    reset({
      is_starred: currentIsStarred,
      is_deleted: currentIsDeleted,
      people_ids: initialPeopleSelections,
      pets_ids: initialPetSelections,
      country_code: initialCountrySelection,
      subdivision_code: initialSubdivisionSelection,
      city: currentCity,
      sub_location: currentSubLocation,
      date_start: currentDateStart,
      date_end: currentDateEnd,
      year: currentYear,
      month: currentMonth,
      day: currentDay,
      sort_by: currentSortBy,
      require_all: currentRequireAll,
    });
  }, [searchParams, reset]);

  // 2) Once allPeople is loaded, replace the “Loading…” labels with real names
  useEffect(() => {
    if (allPeople.length === 0) return;
    const currentPeopleIdsFromUrl = searchParams.getAll("people_ids").map(Number);
    if (currentPeopleIdsFromUrl.length === 0) return;

    const updatedPeopleSelections = currentPeopleIdsFromUrl
      .map((id) => {
        const person = allPeople.find((p) => p.id === id);
        return person ? { value: person.id, label: person.name } : null;
      })
      .filter((x) => x !== null) as { value: number; label: string }[];

    setValue("people_ids", updatedPeopleSelections, { shouldDirty: false });
  }, [allPeople, searchParams, setValue]);

  // 3) Once allPets is loaded, replace the “Loading…” labels for pets
  useEffect(() => {
    if (allPets.length === 0) return;
    const currentPetsIdsFromUrl = searchParams.getAll("pets_ids").map(Number);
    if (currentPetsIdsFromUrl.length === 0) return;

    const updatedPetSelections = currentPetsIdsFromUrl
      .map((id) => {
        const pet = allPets.find((p) => p.id === id);
        return pet ? { value: pet.id, label: pet.name } : null;
      })
      .filter((x) => x !== null) as { value: number; label: string }[];

    setValue("pets_ids", updatedPetSelections, { shouldDirty: false });
  }, [allPets, searchParams, setValue]);

  // 4) Once countries load, populate the country select label
  useEffect(() => {
    if (countries.length === 0) return;
    const countryCode = searchParams.get("country_code");
    if (!countryCode) return;

    const selectedCountry = countries.find((c) => c.alpha2 === countryCode);
    if (!selectedCountry) return;

    setValue(
      "country_code",
      { value: selectedCountry.alpha2, label: selectedCountry.best_name },
      { shouldDirty: false },
    );
  }, [countries, searchParams, setValue]);

  // 5) Once subdivisions load, populate the subdivision select label
  useEffect(() => {
    if (subdivisions.length === 0) return;
    const subCode = searchParams.get("subdivision_code");
    if (!subCode) return;

    const selectedSubdivision = subdivisions.find((s) => s.code === subCode);
    if (!selectedSubdivision) return;

    setValue(
      "subdivision_code",
      { value: selectedSubdivision.code, label: selectedSubdivision.name },
      { shouldDirty: false },
    );
  }, [subdivisions, searchParams, setValue]);

  // Close autocomplete suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        cityAutocompleteRef.current &&
        !cityAutocompleteRef.current.contains(event.target as Node)
      ) {
        setShowCitySuggestions(false);
      }
      if (
        subLocationAutocompleteRef.current &&
        !subLocationAutocompleteRef.current.contains(event.target as Node)
      ) {
        setShowSubLocationSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const filteredCities = useMemo(() => {
    return debouncedCity
      ? cities.filter((c) => c.toLowerCase().includes(debouncedCity.toLowerCase()))
      : cities;
  }, [cities, debouncedCity]);

  const filteredSubLocations = useMemo(() => {
    return debouncedSubLocation
      ? subLocations.filter((loc) =>
          loc.toLowerCase().includes(debouncedSubLocation.toLowerCase()),
        )
      : subLocations;
  }, [subLocations, debouncedSubLocation]);

  const highlightMatch = (text: string, query: string): React.ReactNode => {
    if (!query.trim()) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
    const parts = text.split(regex);
    return parts.map((part, index) =>
      regex.test(part) ? <strong key={index}>{part}</strong> : part,
    );
  };

  const handleCitySelect = (city: string) => {
    setValue("city", city, { shouldDirty: true });
    setShowCitySuggestions(false);
  };

  const handleSubLocationSelect = (location: string) => {
    setValue("sub_location", location, { shouldDirty: true });
    setShowSubLocationSuggestions(false);
  };

  const handleImageClick = (id: number) => {
    navigate(`/images/${id}`);
  };

  // Handle page change
  const handlePageChange = (page: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", page.toString());
    setSearchParams(newParams);
    window.scrollTo(0, 0);
  };

  // Render pagination controls
  const renderPaginationItems = () => {
    const items = [];
    if (totalPages === 0) return null;

    items.push(
      <Pagination.Prev
        key="prev"
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={currentPage === 1}
      />,
    );

    // Always show first page
    items.push(
      <Pagination.Item key={1} active={currentPage === 1} onClick={() => handlePageChange(1)}>
        1
      </Pagination.Item>,
    );

    // Ellipsis for pages far from start
    if (currentPage > 3) {
      items.push(<Pagination.Ellipsis key="ellipsis-start" />);
    }

    // Pages around current page
    const startPage = Math.max(2, currentPage - 1);
    const endPage = Math.min(totalPages - 1, currentPage + 1);
    for (let page = startPage; page <= endPage; page++) {
      items.push(
        <Pagination.Item
          key={page}
          active={page === currentPage}
          onClick={() => handlePageChange(page)}
        >
          {page}
        </Pagination.Item>,
      );
    }

    // Ellipsis for pages far from end
    if (currentPage < totalPages - 2) {
      items.push(<Pagination.Ellipsis key="ellipsis-end" />);
    }

    // Always show last page
    if (totalPages > 1) {
      items.push(
        <Pagination.Item
          key={totalPages}
          active={currentPage === totalPages}
          onClick={() => handlePageChange(totalPages)}
        >
          {totalPages}
        </Pagination.Item>,
      );
    }

    items.push(
      <Pagination.Next
        key="next"
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      />,
    );

    return <Pagination>{items}</Pagination>;
  };

  return (
    <Container fluid className="mt-4">
      <title>Memoria - Image Gallery</title>
      <h2 className="mb-4">Image Gallery</h2>

      <Row>
        {/* Filters Column */}
        <Col md={3}>
          <div className="d-none d-md-block">
            <Card className="shadow-sm">
              <Card.Header className="bg-body-secondary">
                <div className="d-flex justify-content-between align-items-center">
                  <h5 className="mb-0">Filters</h5>
                </div>
              </Card.Header>
              <Card.Body className="p-0">
                <Accordion flush>
                  {/* Quick Filters - Always Visible */}
                  <div className="p-3 border-bottom">
                    <h6 className="text-muted mb-2">QUICK FILTERS</h6>
                    <ButtonGroup className="mb-2 w-100" size="sm">
                      <Button
                        variant={watchedIsStarred ? "primary" : "outline-primary"}
                        onClick={() =>
                          setValue("is_starred", !watchedIsStarred, { shouldDirty: true })
                        }
                      >
                        <i className="fas fa-star me-1"></i>
                        Starred
                      </Button>
                      <Button
                        variant={watchedIsDeleted ? "danger" : "outline-danger"}
                        onClick={() =>
                          setValue("is_deleted", !watchedIsDeleted, { shouldDirty: true })
                        }
                      >
                        <i className="fas fa-trash me-1"></i>
                        Deleted
                      </Button>
                    </ButtonGroup>
                  </div>

                  {/* People & Pets */}
                  <Accordion.Item eventKey="0">
                    <Accordion.Header>
                      <div className="d-flex align-items-center w-100">
                        <i className="fas fa-users me-2"></i>
                        People & Pets
                        {(watchedPeopleIdsValues.length > 0 ||
                          watchedPetsIdsValues.length > 0) && (
                          <Badge bg="success" className="ms-auto me-2">
                            {watchedPeopleIdsValues.length + watchedPetsIdsValues.length}
                          </Badge>
                        )}
                      </div>
                    </Accordion.Header>
                    <Accordion.Body>
                      {/* People Filter */}
                      <Form.Group className="mb-3">
                        <Form.Label>People</Form.Label>
                        <Controller
                          name="people_ids"
                          control={control}
                          render={({ field }) => (
                            <ThemedSelect
                              {...field}
                              isMulti
                              options={allPeople.map((p) => ({ value: p.id, label: p.name }))}
                              isLoading={isLoadingAllPeople}
                              placeholder="Select people."
                              onChange={(selectedOptions) => {
                                field.onChange(selectedOptions);
                              }}
                            />
                          )}
                        />
                      </Form.Group>

                      {/* Pets Filter */}
                      <Form.Group className="mb-3">
                        <Form.Label>Pets</Form.Label>
                        <Controller
                          name="pets_ids"
                          control={control}
                          render={({ field }) => (
                            <ThemedSelect
                              {...field}
                              isMulti
                              options={allPets.map((p) => ({ value: p.id, label: p.name }))}
                              isLoading={isLoadingAllPets}
                              placeholder="Select pets."
                              onChange={(selectedOptions) => {
                                field.onChange(selectedOptions);
                              }}
                            />
                          )}
                        />
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Check
                          type="checkbox"
                          id="requireAll"
                          label="Require ALL selected people/pets to appear"
                          {...control.register("require_all")}
                          checked={watchedRequireAll}
                          onChange={(e) =>
                            setValue("require_all", e.target.checked, { shouldDirty: true })
                          }
                        />
                      </Form.Group>
                    </Accordion.Body>
                  </Accordion.Item>

                  {/* Location */}
                  <Accordion.Item eventKey="1">
                    <Accordion.Header>
                      <div className="d-flex align-items-center w-100">
                        <i className="fas fa-map-marker-alt me-2"></i>
                        Location
                        {(watchedCountryValue || watchedCity) && (
                          <Badge bg="success" className="ms-auto me-2">
                            Active
                          </Badge>
                        )}
                      </div>
                    </Accordion.Header>
                    <Accordion.Body>
                      {/* Location Filters */}
                      <Form.Group className="mb-3">
                        <Form.Label>Country</Form.Label>
                        <Controller
                          name="country_code"
                          control={control}
                          render={({ field }) => (
                            <ThemedSelect
                              {...field}
                              options={countries.map((c) => ({
                                value: c.alpha2,
                                label: c.best_name,
                              }))}
                              isLoading={isLoadingCountries}
                              placeholder="Select country."
                              isClearable
                              onChange={(selectedOption) => {
                                field.onChange(selectedOption);
                                setValue("subdivision_code", null, { shouldDirty: true });
                                setValue("city", "", { shouldDirty: true });
                                setValue("sub_location", "", { shouldDirty: true });
                              }}
                            />
                          )}
                        />
                      </Form.Group>

                      {watchedCountryValue && (
                        <Form.Group className="mb-3">
                          <Form.Label>Subdivision</Form.Label>
                          <Controller
                            name="subdivision_code"
                            control={control}
                            render={({ field }) => (
                              <ThemedSelect
                                {...field}
                                options={subdivisions.map((s) => ({
                                  value: s.code,
                                  label: s.name,
                                }))}
                                isLoading={isLoadingSubdivisions}
                                placeholder="Select subdivision (optional)."
                                isClearable
                                onChange={(selectedOption) => {
                                  field.onChange(selectedOption);
                                  setValue("city", "", { shouldDirty: true });
                                  setValue("sub_location", "", { shouldDirty: true });
                                }}
                              />
                            )}
                          />
                        </Form.Group>
                      )}

                      {watchedCountryValue && (
                        <Form.Group className="mb-3">
                          <Form.Label>City</Form.Label>
                          <div ref={cityAutocompleteRef} className="position-relative">
                            <Controller
                              name="city"
                              control={control}
                              render={({ field }) => (
                                <ThemedSelect
                                  {...field}
                                  options={cities.map((c) => ({ value: c, label: c }))}
                                  isLoading={isLoadingCities}
                                  placeholder="Select city (optional)."
                                  isClearable
                                  onChange={(selectedOption) => {
                                    field.onChange(selectedOption?.value || "");
                                    setValue("sub_location", "", { shouldDirty: true });
                                  }}
                                  value={
                                    watchedCity ? { value: watchedCity, label: watchedCity } : null
                                  }
                                />
                              )}
                            />
                            {isLoadingCities && (
                              <Spinner
                                animation="border"
                                size="sm"
                                className="ms-2 position-absolute top-50 end-0 translate-middle-y"
                              />
                            )}
                            {showCitySuggestions && watchedCity && filteredCities.length > 0 && (
                              <div
                                className="position-absolute w-100 border rounded mt-1 bg-body"
                                style={{
                                  zIndex: 1050,
                                  maxHeight: "200px",
                                  overflowY: "auto",
                                  boxShadow: "0 4px 8px rgba(0,0,0,0.1)",
                                }}
                              >
                                {filteredCities.map((c) => (
                                  <div
                                    key={c}
                                    className="px-3 py-2 cursor-pointer hover-bg-light"
                                    onClick={() => handleCitySelect(c)}
                                    onMouseDown={(e) => e.preventDefault()}
                                  >
                                    {highlightMatch(c, watchedCity)}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </Form.Group>
                      )}

                      {watchedCountryValue && watchedCity && (
                        <Form.Group className="mb-3">
                          <Form.Label>Specific Location</Form.Label>
                          <div ref={subLocationAutocompleteRef} className="position-relative">
                            <Controller
                              name="sub_location"
                              control={control}
                              render={({ field }) => (
                                <ThemedSelect
                                  {...field}
                                  options={subLocations.map((loc) => ({ value: loc, label: loc }))}
                                  isLoading={isLoadingSubLocations}
                                  placeholder="Select location (optional)."
                                  isClearable
                                  onChange={(selectedOption) =>
                                    field.onChange(selectedOption?.value || "")
                                  }
                                  value={
                                    watchedSubLocation
                                      ? { value: watchedSubLocation, label: watchedSubLocation }
                                      : null
                                  }
                                />
                              )}
                            />
                            {isLoadingSubLocations && (
                              <Spinner
                                animation="border"
                                size="sm"
                                className="ms-2 position-absolute top-50 end-0 translate-middle-y"
                              />
                            )}
                            {showSubLocationSuggestions &&
                              watchedSubLocation &&
                              filteredSubLocations.length > 0 && (
                                <div
                                  className="position-absolute w-100 border rounded mt-1 bg-body"
                                  style={{
                                    zIndex: 1050,
                                    maxHeight: "200px",
                                    overflowY: "auto",
                                    boxShadow: "0 4px 8px rgba(0,0,0,0.1)",
                                  }}
                                >
                                  {filteredSubLocations.map((loc) => (
                                    <div
                                      key={loc}
                                      className="px-3 py-2 cursor-pointer hover-bg-light"
                                      onClick={() => handleSubLocationSelect(loc)}
                                      onMouseDown={(e) => e.preventDefault()}
                                    >
                                      {highlightMatch(loc, watchedSubLocation)}
                                    </div>
                                  ))}
                                </div>
                              )}
                          </div>
                        </Form.Group>
                      )}
                    </Accordion.Body>
                  </Accordion.Item>

                  {/* Date & Time */}
                  <Accordion.Item eventKey="2">
                    <Accordion.Header>
                      <div className="d-flex align-items-center w-100">
                        <i className="fas fa-calendar me-2"></i>
                        Date & Time
                        {(watchedDateStart || watchedDateEnd || watchedYear) && (
                          <Badge bg="success" className="ms-auto me-2">
                            Active
                          </Badge>
                        )}
                      </div>
                    </Accordion.Header>
                    <Accordion.Body>
                      {/* Date Range Filters */}
                      <Form.Group className="mb-3">
                        <Form.Label>Date Start</Form.Label>
                        <Form.Control
                          type="date"
                          {...control.register("date_start")}
                          value={watchedDateStart}
                          onChange={(e) =>
                            setValue("date_start", e.target.value, { shouldDirty: true })
                          }
                        />
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Label>Date End</Form.Label>
                        <Form.Control
                          type="date"
                          {...control.register("date_end")}
                          value={watchedDateEnd}
                          onChange={(e) =>
                            setValue("date_end", e.target.value, { shouldDirty: true })
                          }
                        />
                      </Form.Group>

                      {/* Exact Date Filters */}
                      <Form.Group className="mb-3">
                        <Form.Label>Exact Year</Form.Label>
                        <Form.Control
                          type="number"
                          placeholder="YYYY"
                          {...control.register("year", { valueAsNumber: true })}
                          value={watchedYear || ""}
                          onChange={(e) =>
                            setValue(
                              "year",
                              e.target.value ? parseInt(e.target.value, 10) : null,
                              {
                                shouldDirty: true,
                              },
                            )
                          }
                        />
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Label>Exact Month</Form.Label>
                        <Form.Control
                          type="number"
                          placeholder="MM (1-12)"
                          min="1"
                          max="12"
                          disabled={!watchedYear}
                          {...control.register("month", {
                            valueAsNumber: true,
                            min: { value: 1, message: "Month must be between 1 and 12" },
                            max: { value: 12, message: "Month must be between 1 and 12" },
                          })}
                          value={watchedMonth || ""}
                          onChange={(e) => {
                            const newMonth = e.target.value ? parseInt(e.target.value, 10) : null;
                            setValue("month", newMonth, { shouldDirty: true });
                            // Clear day when month changes
                            if (!newMonth) {
                              setValue("day", null, { shouldDirty: true });
                            }
                          }}
                        />
                        {!watchedYear && (
                          <Form.Text className="text-muted">
                            Requires a year to be selected first
                          </Form.Text>
                        )}
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Label>Exact Day</Form.Label>
                        <Form.Control
                          type="number"
                          placeholder="DD (1-31)"
                          min="1"
                          max="31"
                          disabled={!watchedMonth}
                          {...control.register("day", {
                            valueAsNumber: true,
                            min: { value: 1, message: "Day must be between 1 and 31" },
                            max: { value: 31, message: "Day must be between 1 and 31" },
                          })}
                          value={watchedDay || ""}
                          onChange={(e) =>
                            setValue("day", e.target.value ? parseInt(e.target.value, 10) : null, {
                              shouldDirty: true,
                            })
                          }
                        />
                        {!watchedMonth && (
                          <Form.Text className="text-muted">
                            Requires a month to be selected first
                          </Form.Text>
                        )}
                      </Form.Group>
                    </Accordion.Body>
                  </Accordion.Item>

                  {/* Advanced Options */}
                  <Accordion.Item eventKey="3">
                    <Accordion.Header>
                      <div className="d-flex align-items-center w-100">
                        <i className="fas fa-cog me-2"></i>
                        Advanced
                        {watchedRequireAll && (
                          <Badge bg="success" className="ms-auto me-2">
                            Active
                          </Badge>
                        )}
                      </div>
                    </Accordion.Header>
                    <Accordion.Body>
                      {/* Sort By Filter */}
                      <Form.Group className="mb-3">
                        <Form.Label>Sort By</Form.Label>
                        <Form.Select
                          {...control.register("sort_by")}
                          value={watchedSortBy}
                          onChange={(e) =>
                            setValue(
                              "sort_by",
                              e.target.value as ImageFilterFormInputs["sort_by"],
                              {
                                shouldDirty: true,
                              },
                            )
                          }
                        >
                          <option value="pk">Default (ID)</option>
                          <option value="created_at">Created (Ascending)</option>
                          <option value="-created_at">Created (Descending)</option>
                          <option value="updated_at">Modified (Ascending)</option>
                          <option value="-updated_at">Modified (Descending)</option>
                          <option value="title">Title (Ascending)</option>
                          <option value="-title">Title (Descending)</option>
                        </Form.Select>
                      </Form.Group>
                    </Accordion.Body>
                  </Accordion.Item>
                </Accordion>
              </Card.Body>
              <Card.Footer className="bg-body-secondary">
                <div className="d-grid gap-2">
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    onClick={() => {
                      reset();
                      setSearchParams(new URLSearchParams());
                    }}
                    disabled={!isDirty && searchParams.toString() === ""}
                  >
                    Clear All
                  </Button>
                </div>
              </Card.Footer>
            </Card>
          </div>
        </Col>

        {/* Image Gallery Column */}
        <Col md={9}>
          {isLoadingImages && !isPlaceholderData ? (
            <div className="text-center my-5">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading images...</span>
              </Spinner>
              <p className="mt-2">Loading images...</p>
            </div>
          ) : isErrorImages ? (
            <Alert variant="danger" className="mt-4">
              Error loading images: {imagesError?.message || "An unknown error occurred."}
            </Alert>
          ) : images.length === 0 ? (
            <Alert variant="info" className="mt-4">
              No images found matching your criteria.
            </Alert>
          ) : (
            <>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h3>Images ({totalImages})</h3>
                <small className="text-muted">
                  Showing {offset + 1}-{Math.min(offset + pageSize, totalImages)} of {totalImages}
                </small>
              </div>
              <ImageWall images={images} onImageClick={handleImageClick} columns={3} />
              {totalPages > 1 && (
                <div className="d-flex justify-content-center mt-4">{renderPaginationItems()}</div>
              )}
            </>
          )}
        </Col>
      </Row>
    </Container>
  );
};

export default ImageGalleryPage;
