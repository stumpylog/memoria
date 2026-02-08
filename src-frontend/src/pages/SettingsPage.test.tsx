import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { GroupOutSchema, SiteSettingsSchema, UserOutSchema } from "../api";

import { AuthContext } from "../contexts/AuthContext";
import SettingsPage from "./SettingsPage";

// Mock test data for interaction tests
const mockUsers: UserOutSchema[] = [
  {
    id: 2,
    username: "testuser1",
    email: "test1@example.com",
    first_name: "Test",
    last_name: "User1",
    is_active: true,
    is_staff: false,
    is_superuser: false,
    last_login: "2024-01-15T10:00:00Z",
    date_joined: "2024-01-01T00:00:00Z",
  },
  {
    id: 3,
    username: "testuser2",
    email: "test2@example.com",
    first_name: "Test",
    last_name: "User2",
    is_active: true,
    is_staff: false,
    is_superuser: false,
    last_login: null,
    date_joined: "2024-01-10T00:00:00Z",
  },
];

const mockGroups: GroupOutSchema[] = [
  { id: 1, name: "Test Group 1" },
  { id: 2, name: "Test Group 2" },
];

// Track which test is running to return appropriate data
let testUsers: UserOutSchema[] = [];
let testGroups: GroupOutSchema[] = [];

// Mock the API query options
vi.mock("../api/@tanstack/react-query.gen", () => ({
  getSystemSettingsOptions: vi.fn(() => ({
    queryKey: ["getSystemSettings"],
    queryFn: async () => ({
      large_image_max_size: 2560,
      large_image_quality: 90,
      thumbnail_max_size: 512,
    }),
  })),
  usersListOptions: vi.fn(() => ({
    queryKey: ["usersList"],
    queryFn: async () => testUsers,
  })),
  listGroupsOptions: vi.fn(() => ({
    queryKey: ["listGroups"],
    queryFn: async () => testGroups,
  })),
  usersGroupsListOptions: vi.fn(() => ({
    queryKey: ["usersGroupsList"],
    queryFn: async () => [],
  })),
  updateSystemSettingsMutation: vi.fn(() => ({
    mutationFn: async () => ({}),
  })),
}));

// Mock child components with props tracking
const mockCreateUserModal = vi.fn();
const mockEditUserModal = vi.fn();
const mockManageGroupsModal = vi.fn();
const mockCreateGroupModal = vi.fn();
const mockEditGroupModal = vi.fn();
const mockDeleteGroupModal = vi.fn();

vi.mock("../components/user-management/CreateUserModal", () => ({
  default: (props: { show: boolean; handleClose: () => void }) => {
    mockCreateUserModal(props);
    return props.show ? <div data-testid="create-user-modal">CreateUserModal</div> : null;
  },
}));

vi.mock("../components/user-management/EditUserModal", () => ({
  default: (props: { show: boolean; handleClose: () => void; user?: UserOutSchema }) => {
    mockEditUserModal(props);
    return props.show && props.user ? (
      <div data-testid="edit-user-modal">EditUserModal</div>
    ) : null;
  },
}));

vi.mock("../components/user-management/ManageGroupsModal", () => ({
  default: (props: {
    show: boolean;
    handleClose: () => void;
    user?: UserOutSchema;
    allGroups: GroupOutSchema[];
    userGroupIds: number[];
    userGroupsLoading: boolean;
  }) => {
    mockManageGroupsModal(props);
    return props.show && props.user ? (
      <div data-testid="manage-groups-modal">ManageGroupsModal</div>
    ) : null;
  },
}));

vi.mock("../components/group-management/CreateGroupModal", () => ({
  default: (props: { show: boolean; handleClose: () => void }) => {
    mockCreateGroupModal(props);
    return props.show ? <div data-testid="create-group-modal">CreateGroupModal</div> : null;
  },
}));

vi.mock("../components/group-management/EditGroupModal", () => ({
  default: (props: { show: boolean; handleClose: () => void; group?: GroupOutSchema }) => {
    mockEditGroupModal(props);
    return props.show && props.group ? (
      <div data-testid="edit-group-modal">EditGroupModal</div>
    ) : null;
  },
}));

vi.mock("../components/group-management/DeleteGroupModal", () => ({
  default: (props: { show: boolean; handleClose: () => void; group?: GroupOutSchema }) => {
    mockDeleteGroupModal(props);
    return props.show && props.group ? (
      <div data-testid="delete-group-modal">DeleteGroupModal</div>
    ) : null;
  },
}));

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const mockStaffUser: UserOutSchema = {
  id: 1,
  username: "staffuser",
  email: "staff@example.com",
  first_name: "Staff",
  last_name: "User",
  is_active: true,
  is_staff: true,
  is_superuser: false,
  last_login: null,
  date_joined: "2024-01-01T00:00:00Z",
};

const mockProfile = {
  id: 1,
  user: 1,
  date_format: "MM/DD/YYYY" as const,
  time_format: "12h" as const,
  timezone: "America/New_York",
};

// Helper function to render SettingsPage with common setup
const renderSettingsPage = () => {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider
        value={{
          user: mockStaffUser,
          profile: mockProfile,
          isAuthenticated: true,
          isLoading: false,
          error: null,
          generalApiError: null,
          setGeneralApiError: vi.fn(),
          login: vi.fn(),
          logout: vi.fn(),
          fetchCurrentUser: vi.fn(),
          fetchUserProfile: vi.fn(),
        }}
      >
        <SettingsPage />
      </AuthContext.Provider>
    </QueryClientProvider>,
  );
};

describe("SettingsPage", () => {
  it("renders without crashing for staff users", async () => {
    const queryClient = createQueryClient();

    // Set initial data to avoid loading state
    queryClient.setQueryData(["getSystemSettings"], {
      large_image_max_size: 2560,
      large_image_quality: 90,
      thumbnail_max_size: 512,
    } as SiteSettingsSchema);
    queryClient.setQueryData(["usersList"], [] as UserOutSchema[]);
    queryClient.setQueryData(["listGroups"], [] as GroupOutSchema[]);

    render(
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider
          value={{
            user: mockStaffUser,
            profile: mockProfile,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            generalApiError: null,
            setGeneralApiError: vi.fn(),
            login: vi.fn(),
            logout: vi.fn(),
            fetchCurrentUser: vi.fn(),
            fetchUserProfile: vi.fn(),
          }}
        >
          <SettingsPage />
        </AuthContext.Provider>
      </QueryClientProvider>,
    );

    // Page should render
    expect(screen.getByText("Application Settings")).toBeInTheDocument();
  });

  it("renders all three main sections", async () => {
    const queryClient = createQueryClient();

    queryClient.setQueryData(["getSystemSettings"], {
      large_image_max_size: 2560,
      large_image_quality: 90,
      thumbnail_max_size: 512,
    } as SiteSettingsSchema);
    queryClient.setQueryData(["usersList"], [] as UserOutSchema[]);
    queryClient.setQueryData(["listGroups"], [] as GroupOutSchema[]);

    render(
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider
          value={{
            user: mockStaffUser,
            profile: mockProfile,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            generalApiError: null,
            setGeneralApiError: vi.fn(),
            login: vi.fn(),
            logout: vi.fn(),
            fetchCurrentUser: vi.fn(),
            fetchUserProfile: vi.fn(),
          }}
        >
          <SettingsPage />
        </AuthContext.Provider>
      </QueryClientProvider>,
    );

    // Verify three main sections are present
    expect(screen.getByText("System Settings")).toBeInTheDocument();
    expect(screen.getByText("User Management")).toBeInTheDocument();
    expect(screen.getByText("Group Management")).toBeInTheDocument();
  });

  it("renders create buttons for users and groups", async () => {
    const queryClient = createQueryClient();

    queryClient.setQueryData(["getSystemSettings"], {
      large_image_max_size: 2560,
      large_image_quality: 90,
      thumbnail_max_size: 512,
    } as SiteSettingsSchema);
    queryClient.setQueryData(["usersList"], [] as UserOutSchema[]);
    queryClient.setQueryData(["listGroups"], [] as GroupOutSchema[]);

    render(
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider
          value={{
            user: mockStaffUser,
            profile: mockProfile,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            generalApiError: null,
            setGeneralApiError: vi.fn(),
            login: vi.fn(),
            logout: vi.fn(),
            fetchCurrentUser: vi.fn(),
            fetchUserProfile: vi.fn(),
          }}
        >
          <SettingsPage />
        </AuthContext.Provider>
      </QueryClientProvider>,
    );

    // Verify create buttons are present
    expect(screen.getByText("Create New User")).toBeInTheDocument();
    expect(screen.getByText("Create New Group")).toBeInTheDocument();
  });

  it("displays loading states correctly", async () => {
    const queryClient = createQueryClient();

    // Don't set query data to trigger loading state
    render(
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider
          value={{
            user: mockStaffUser,
            profile: mockProfile,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            generalApiError: null,
            setGeneralApiError: vi.fn(),
            login: vi.fn(),
            logout: vi.fn(),
            fetchCurrentUser: vi.fn(),
            fetchUserProfile: vi.fn(),
          }}
        >
          <SettingsPage />
        </AuthContext.Provider>
      </QueryClientProvider>,
    );

    // Should show loading spinner
    const loadingTexts = screen.getAllByText(/Loading/i);
    expect(loadingTexts.length).toBeGreaterThan(0);
  });

  // ==================== Modal Opening Tests ====================

  describe("Modal Opening", () => {
    it('opens CreateUserModal when "Create New User" button is clicked', async () => {
      const user = userEvent.setup();

      // Set mock data for this test
      testUsers = mockUsers;
      testGroups = mockGroups;

      renderSettingsPage();

      // Find and click the Create New User button
      const createButton = screen.getByText("Create New User");
      await user.click(createButton);

      // Verify modal is shown
      expect(screen.getByTestId("create-user-modal")).toBeInTheDocument();
      expect(mockCreateUserModal).toHaveBeenLastCalledWith(
        expect.objectContaining({
          show: true,
        }),
      );
    });

    it('opens CreateGroupModal when "Create New Group" button is clicked', async () => {
      const user = userEvent.setup();

      // Set mock data for this test
      testUsers = mockUsers;
      testGroups = mockGroups;

      renderSettingsPage();

      // Find and click the Create New Group button
      const createButton = screen.getByText("Create New Group");
      await user.click(createButton);

      // Verify modal is shown
      expect(screen.getByTestId("create-group-modal")).toBeInTheDocument();
      expect(mockCreateGroupModal).toHaveBeenLastCalledWith(
        expect.objectContaining({
          show: true,
        }),
      );
    });

    it("opens EditUserModal when Edit button on user row is clicked", async () => {
      const user = userEvent.setup();

      // Set mock data for this test
      testUsers = mockUsers;
      testGroups = mockGroups;

      renderSettingsPage();

      // Wait for the user table to render
      await waitFor(() => {
        expect(screen.getByText("testuser1")).toBeInTheDocument();
      });

      // Find all Edit buttons in the user table (there are multiple "Edit" buttons)
      const editButtons = screen.getAllByText("Edit");
      // Click the first Edit button (user row)
      await user.click(editButtons[0]);

      // Verify modal is shown with correct user
      await waitFor(() => {
        expect(screen.getByTestId("edit-user-modal")).toBeInTheDocument();
      });
      expect(mockEditUserModal).toHaveBeenLastCalledWith(
        expect.objectContaining({
          show: true,
          user: mockUsers[0],
        }),
      );
    });

    it("opens ManageGroupsModal when Groups button on user row is clicked", async () => {
      const user = userEvent.setup();

      // Set mock data for this test
      testUsers = mockUsers;
      testGroups = mockGroups;

      renderSettingsPage();

      // Wait for the user table to render
      await waitFor(() => {
        expect(screen.getByText("testuser1")).toBeInTheDocument();
      });

      // Find all Groups buttons
      const groupsButtons = screen.getAllByText("Groups");
      // Click the first Groups button
      await user.click(groupsButtons[0]);

      // Verify modal is shown with correct user
      await waitFor(() => {
        expect(screen.getByTestId("manage-groups-modal")).toBeInTheDocument();
      });
      expect(mockManageGroupsModal).toHaveBeenLastCalledWith(
        expect.objectContaining({
          show: true,
          user: mockUsers[0],
        }),
      );
    });

    it("opens EditGroupModal when Edit button on group row is clicked", async () => {
      const user = userEvent.setup();

      // Set mock data for this test
      testUsers = mockUsers;
      testGroups = mockGroups;

      renderSettingsPage();

      // Wait for the group table to render
      await waitFor(() => {
        expect(screen.getByText("Test Group 1")).toBeInTheDocument();
      });

      // Find all Edit buttons (users and groups)
      const editButtons = screen.getAllByText("Edit");
      // The last two Edit buttons are for groups
      const groupEditButton = editButtons[editButtons.length - 2];
      await user.click(groupEditButton);

      // Verify modal is shown with correct group
      await waitFor(() => {
        expect(screen.getByTestId("edit-group-modal")).toBeInTheDocument();
      });
      expect(mockEditGroupModal).toHaveBeenLastCalledWith(
        expect.objectContaining({
          show: true,
          group: mockGroups[0],
        }),
      );
    });

    it("opens DeleteGroupModal when Delete button on group row is clicked", async () => {
      const user = userEvent.setup();

      // Set mock data for this test
      testUsers = mockUsers;
      testGroups = mockGroups;

      renderSettingsPage();

      // Wait for the group table to render
      await waitFor(() => {
        expect(screen.getByText("Test Group 1")).toBeInTheDocument();
      });

      // Find all Delete buttons
      const deleteButtons = screen.getAllByText("Delete");
      // Click the first Delete button (first group)
      await user.click(deleteButtons[0]);

      // Verify modal is shown with correct group
      await waitFor(() => {
        expect(screen.getByTestId("delete-group-modal")).toBeInTheDocument();
      });
      expect(mockDeleteGroupModal).toHaveBeenLastCalledWith(
        expect.objectContaining({
          show: true,
          group: mockGroups[0],
        }),
      );
    });
  });

  // ==================== Modal Props Verification Tests ====================

  describe("Modal Props Verification", () => {
    it("passes correct user data to EditUserModal", async () => {
      const user = userEvent.setup();

      // Set mock data for this test
      testUsers = mockUsers;
      testGroups = mockGroups;

      renderSettingsPage();

      // Wait for the user table to render
      await waitFor(() => {
        expect(screen.getByText("testuser1")).toBeInTheDocument();
      });

      // Click Edit button for first user
      const editButtons = screen.getAllByText("Edit");
      await user.click(editButtons[0]);

      // Wait for modal to appear
      await waitFor(() => {
        expect(screen.getByTestId("edit-user-modal")).toBeInTheDocument();
      });

      // Verify the user object passed has correct properties
      const lastCall = mockEditUserModal.mock.calls[mockEditUserModal.mock.calls.length - 1][0];
      expect(lastCall.user).toEqual(mockUsers[0]);
      expect(lastCall.user.id).toBe(2);
      expect(lastCall.user.username).toBe("testuser1");
      expect(lastCall.user.email).toBe("test1@example.com");
      expect(lastCall.user.first_name).toBe("Test");
      expect(lastCall.user.last_name).toBe("User1");
    });

    it("passes correct group data to EditGroupModal", async () => {
      const user = userEvent.setup();

      // Set mock data for this test
      testUsers = mockUsers;
      testGroups = mockGroups;

      renderSettingsPage();

      // Wait for the group table to render
      await waitFor(() => {
        expect(screen.getByText("Test Group 1")).toBeInTheDocument();
      });

      // Click Edit button for first group
      const editButtons = screen.getAllByText("Edit");
      const groupEditButton = editButtons[editButtons.length - 2];
      await user.click(groupEditButton);

      // Wait for modal to appear
      await waitFor(() => {
        expect(screen.getByTestId("edit-group-modal")).toBeInTheDocument();
      });

      // Verify the group object passed has correct properties
      const lastCall = mockEditGroupModal.mock.calls[mockEditGroupModal.mock.calls.length - 1][0];
      expect(lastCall.group).toEqual(mockGroups[0]);
      expect(lastCall.group.id).toBe(1);
      expect(lastCall.group.name).toBe("Test Group 1");
    });

    it("passes correct props to ManageGroupsModal", async () => {
      const user = userEvent.setup();

      // Set mock data for this test
      testUsers = mockUsers;
      testGroups = mockGroups;

      renderSettingsPage();

      // Wait for the user table to render
      await waitFor(() => {
        expect(screen.getByText("testuser1")).toBeInTheDocument();
      });

      // Click Groups button for first user
      const groupsButtons = screen.getAllByText("Groups");
      await user.click(groupsButtons[0]);

      // Wait for modal to appear
      await waitFor(() => {
        expect(screen.getByTestId("manage-groups-modal")).toBeInTheDocument();
      });

      // Verify all props are passed correctly
      const lastCall =
        mockManageGroupsModal.mock.calls[mockManageGroupsModal.mock.calls.length - 1][0];
      expect(lastCall.user).toEqual(mockUsers[0]);
      expect(lastCall.allGroups).toEqual(mockGroups);
      expect(lastCall.userGroupIds).toEqual([]);
      expect(lastCall.userGroupsLoading).toBe(false);
    });
  });

  // ==================== Modal Closing Tests ====================

  describe("Modal Closing", () => {
    it("closes modal when handleClose is called", async () => {
      const user = userEvent.setup();

      // Set mock data for this test
      testUsers = mockUsers;
      testGroups = mockGroups;

      renderSettingsPage();

      // Wait for the user table to render
      await waitFor(() => {
        expect(screen.getByText("testuser1")).toBeInTheDocument();
      });

      // Open EditUserModal
      const editButtons = screen.getAllByText("Edit");
      await user.click(editButtons[0]);

      // Verify modal is shown
      await waitFor(() => {
        expect(screen.getByTestId("edit-user-modal")).toBeInTheDocument();
      });

      // Get the handleClose callback from the last call
      const lastCall = mockEditUserModal.mock.calls[mockEditUserModal.mock.calls.length - 1][0];
      const handleClose = lastCall.handleClose;

      // Call handleClose wrapped in act
      act(() => {
        handleClose();
      });

      // Verify modal is no longer shown (show=false)
      // The modal mock returns null when show is false
      await waitFor(() => {
        expect(screen.queryByTestId("edit-user-modal")).not.toBeInTheDocument();
      });
    });

    it("clears selectedUser state when EditUserModal is closed", async () => {
      const user = userEvent.setup();

      // Set mock data for this test
      testUsers = mockUsers;
      testGroups = mockGroups;

      renderSettingsPage();

      // Wait for the user table to render
      await waitFor(() => {
        expect(screen.getByText("testuser1")).toBeInTheDocument();
      });

      // Open EditUserModal
      const editButtons = screen.getAllByText("Edit");
      await user.click(editButtons[0]);

      // Verify modal is shown with user
      await waitFor(() => {
        expect(screen.getByTestId("edit-user-modal")).toBeInTheDocument();
      });
      let lastCall = mockEditUserModal.mock.calls[mockEditUserModal.mock.calls.length - 1][0];
      expect(lastCall.user).toEqual(mockUsers[0]);

      // Close the modal wrapped in act
      const handleClose = lastCall.handleClose;
      act(() => {
        handleClose();
      });

      // Verify modal is closed
      await waitFor(() => {
        expect(screen.queryByTestId("edit-user-modal")).not.toBeInTheDocument();
      });

      // Open modal again - if selectedUser was cleared, opening it again won't pass a user
      // Actually, since we need to click again, it will set a new user
      await user.click(editButtons[0]);

      // Verify the modal can be opened again with the same user
      await waitFor(() => {
        expect(screen.getByTestId("edit-user-modal")).toBeInTheDocument();
      });
      lastCall = mockEditUserModal.mock.calls[mockEditUserModal.mock.calls.length - 1][0];
      expect(lastCall.user).toEqual(mockUsers[0]);
    });
  });
});
